"""
    Performance Indicators for DRKCM

    License: MIT
"""

from dateutil.relativedelta import relativedelta
from io import BytesIO

from gluon import current, HTTP

from core import CRUDMethod, XLSWriter, s3_decode_iso_datetime, s3_str

# =============================================================================
class PerformanceIndicators:
    """ Default Performance Indicators Set (Base Class) """

    def __init__(self):

        self.styles = None

    # -------------------------------------------------------------------------
    @staticmethod
    def compute(resource):
        """
            Query/compute the performance indicators

            Args:
                resource: the filtered dvr_response_action resource

            Returns:
                dict with performance indicators (raw values)
        """

        db = current.db
        s3db = current.s3db

        table = resource.table
        rows = resource.select(["id"], as_rows=True)

        # Master query
        record_ids = set(row.id for row in rows)
        master_query = table._id.belongs(record_ids)

        # Total clients
        num_clients = table.person_id.count(distinct=True)
        row = db(master_query).select(num_clients).first()
        total_clients = row[num_clients]

        # Total number of consultations, average effort per consultation
        ttable = s3db.dvr_response_type
        if current.deployment_settings.get_dvr_response_types():
            join = ttable.on((ttable.id == table.response_type_id) & \
                             (ttable.is_consultation == True))
        else:
            # Count all responses
            join = None
        num_responses = table._id.count()
        avg_hours = table.hours.avg()
        row = db(master_query).select(num_responses,
                                      avg_hours,
                                      join = join,
                                      ).first()
        total_responses = row[num_responses]
        avg_hours_per_response = row[avg_hours]

        # Average number of consultations per client
        if total_clients:
            avg_responses_per_client = total_responses / total_clients
        else:
            avg_responses_per_client = 0

        # Return indicators
        return {"total_responses": total_responses,
                "total_clients": total_clients,
                "avg_hours_per_response": avg_hours_per_response,
                "avg_responses_per_client": avg_responses_per_client,
                }

    # -------------------------------------------------------------------------
    def export(self, resource, sheet, title, subtitle=None):
        """
            Export performance indicators

            Args:
                resource: the CRUDResource
                sheet: the XLS worksheet to write to
                title: the title for the export
                subtitle: an optional subtitle (e.g. start+end dates)
        """

        T = current.T

        indicators = self.compute(resource)

        write = self.write
        rowindex = 0

        # Title
        write(sheet, rowindex, 0, title, style="header")
        rowindex += 1

        # Subtitle (optional)
        if subtitle:
            write(sheet, rowindex, 0, subtitle)
            rowindex += 2
        else:
            rowindex += 1

        # Basic performance indicators
        write(sheet, rowindex, 0, T("Total Number of Consultations"))
        write(sheet, rowindex, 1, indicators.get("total_responses", ""))
        rowindex += 1

        write(sheet, rowindex, 0, T("Total Number of Clients"))
        write(sheet, rowindex, 1, indicators.get("total_clients", ""))
        rowindex += 1

        write(sheet, rowindex, 0, T("Average Duration of Consultations (minutes)"))
        avg_hours_per_response = indicators.get("avg_hours_per_response")
        if avg_hours_per_response:
            avg_minutes_per_response = int(round(avg_hours_per_response * 60))
        else:
            avg_minutes_per_response = ""
        write(sheet, rowindex, 1, avg_minutes_per_response)
        rowindex += 1

        write(sheet, rowindex, 0, T("Average Number of Consultations per Client"))
        write(sheet, rowindex, 1, indicators.get("avg_responses_per_client", ""))
        rowindex += 2

    # -------------------------------------------------------------------------
    def write(self, sheet, rowindex, colindex, label, style="odd"):
        """
            Write a label/value into the XLS worksheet

            Args:
                sheet: the worksheet
                rowindex: the row index
                colindex: the column index
                label: the label/value to write
                style: style name (XLSWriter styles)
        """

        styles = self.styles
        if not styles:
            self.styles = styles = XLSWriter._styles()

        style = styles.get(style)
        if not style:
            import xlwt
            style = xlwt.XFStyle()

        label = s3_str(label)

        # Adjust column width
        col = sheet.col(colindex)
        curwidth = col.width or 0
        adjwidth = max(len(label) * 240, 2480) if label else 2480
        col.width = max(curwidth, adjwidth)

        row = sheet.row(rowindex)
        row.write(colindex, label, style)

# =============================================================================
class PerformanceIndicatorsLEA(PerformanceIndicators):
    """ LEA-specific Performance Indicators Set """

    # -------------------------------------------------------------------------
    @staticmethod
    def compute(resource):
        """
            Query/compute the performance indicators

            Args:
                resource: the filtered dvr_response_action resource

            Returns:
                dict with performance indicators (raw values)
        """
        # TODO adjust to only include efforts of SB/VB (exclude AVB-efforts)

        db = current.db
        s3db = current.s3db

        table = resource.table
        rows = resource.select(["id"], as_rows=True)

        # Master query
        record_ids = set(row.id for row in rows)
        master_query = table._id.belongs(record_ids)

        # Total responses
        total_responses = len(record_ids)

        # Total clients, average effort per response
        num_clients = table.person_id.count(distinct=True)
        avg_hours = table.hours.avg()

        row = db(master_query).select(num_clients,
                                      avg_hours,
                                      ).first()
        total_clients = row[num_clients]
        avg_hours_per_response = row[avg_hours]

        # Average number of responses per client
        if total_clients:
            avg_responses_per_client = total_responses / total_clients
        else:
            avg_responses_per_client = 0

        # Number of clients without family members in case group
        ctable = s3db.dvr_case
        join = ctable.on((ctable.person_id == table.person_id) & \
                         (ctable.household_size == 1))

        num_clients = table.person_id.count(distinct=True)

        row = db(master_query).select(num_clients,
                                      join = join,
                                      ).first()
        singles = row[num_clients]
        families = total_clients - singles

        # Top 5 Nationalities
        dtable = s3db.pr_person_details
        left = dtable.on(dtable.person_id == table.person_id)

        nationality = dtable.nationality
        num_clients = table.person_id.count(distinct=True)

        rows = db(master_query).select(nationality,
                                       groupby = nationality,
                                       orderby = ~num_clients,
                                       left = left,
                                       limitby = (0, 5),
                                       )
        top_5_nationalities = [row[nationality] for row in rows]

        # Top 5 Needs (only possible if using themes+needs)
        if current.deployment_settings.get_dvr_response_themes_needs():

            ltable = s3db.dvr_response_action_theme
            ttable = s3db.dvr_response_theme
            left = ttable.on(ttable.id == ltable.theme_id)

            num_responses = ltable.action_id.count(distinct=True)
            need = ttable.need_id

            query = ltable.action_id.belongs(record_ids)
            rows = db(query).select(need,
                                    groupby = need,
                                    orderby = ~num_responses,
                                    left = left,
                                    limitby = (0, 5),
                                    )
            top_5_needs = [row[need] for row in rows]
        else:
            top_5_needs = None

        # Return indicators
        return {"total_responses": total_responses,
                "total_clients": total_clients,
                "avg_hours_per_response": avg_hours_per_response,
                "avg_responses_per_client": avg_responses_per_client,
                "top_5_nationalities": top_5_nationalities,
                "top_5_needs": top_5_needs,
                "singles": singles,
                "families": families,
                }

    # -------------------------------------------------------------------------
    def export(self, resource, sheet, title, subtitle=None):
        """
            Export performance indicators

            Args:
                resource: the CRUDResource
                sheet: the XLS worksheet to write to
                title: the title for the export
                subtitle: an optional subtitle (e.g. start+end dates)
        """

        T = current.T
        s3db = current.s3db

        indicators = self.compute(resource)

        write = self.write
        rowindex = 0

        # Title
        write(sheet, rowindex, 0, title, style="header")
        rowindex += 1

        # Subtitle (optional)
        if subtitle:
            write(sheet, rowindex, 0, subtitle)
            rowindex += 2
        else:
            rowindex += 1

        # Basic performance indicators
        write(sheet, rowindex, 0, T("Total Number of Consultations"))
        write(sheet, rowindex, 1, indicators.get("total_responses", ""))
        rowindex += 1

        write(sheet, rowindex, 0, T("Total Number of Clients"))
        write(sheet, rowindex, 1, indicators.get("total_clients", ""))
        rowindex += 1

        write(sheet, rowindex, 0, T("Average Duration of Consultations (minutes)"))
        avg_hours_per_response = indicators.get("avg_hours_per_response")
        if avg_hours_per_response:
            avg_minutes_per_response = int(round(avg_hours_per_response * 60))
        else:
            avg_minutes_per_response = ""
        write(sheet, rowindex, 1, avg_minutes_per_response)
        rowindex += 1

        write(sheet, rowindex, 0, T("Average Number of Consultations per Client"))
        write(sheet, rowindex, 1, indicators.get("avg_responses_per_client", ""))
        rowindex += 2

        # Distribution
        write(sheet, rowindex, 0, T("Distribution of Clients"))
        write(sheet, rowindex, 1, T("Single"))
        write(sheet, rowindex, 2, indicators.get("singles", ""))
        rowindex += 1

        write(sheet, rowindex, 1, T("Family"))
        write(sheet, rowindex, 2, indicators.get("families", ""))
        rowindex += 1

        write(sheet, rowindex, 1, T("Group Counseling"))
        rowindex += 1

        write(sheet, rowindex, 1, T("Individual Counseling"))
        write(sheet, rowindex, 2, indicators.get("total_responses", ""))
        rowindex += 2

        # Top-5's
        write(sheet, rowindex, 0, T("Top 5 Countries of Origin"))
        top_5_nationalities = indicators.get("top_5_nationalities")
        if top_5_nationalities:
            dtable = s3db.pr_person_details
            field = dtable.nationality
            for rank, nationality in enumerate(top_5_nationalities):
                write(sheet, rowindex, 1, "%s - %s" % (rank + 1, field.represent(nationality)))
                rowindex += 1

        rowindex += 1
        write(sheet, rowindex, 0, T("Top 5 Counseling Reasons"))
        top_5_needs = indicators.get("top_5_needs")
        if top_5_needs:
            ttable = s3db.dvr_response_theme
            field = ttable.need_id
            for rank, need in enumerate(top_5_needs):
                write(sheet, rowindex, 1, "%s - %s" % (rank + 1, field.represent(need)))
                rowindex += 1

# =============================================================================
class PerformanceIndicatorsBAMF(PerformanceIndicators):

    sector = "AVB"

    # -------------------------------------------------------------------------
    def __init__(self):

        super().__init__()

        self._sector_id = None

    # -------------------------------------------------------------------------
    def compute(self, resource):
        """
            Query/compute the performance indicators

            Args:
                resource: the filtered dvr_response_action resource

            Returns:
                dict with performance indicators (raw values)
        """

        rows = resource.select(["id"], as_rows=True)
        subset = {row.id for row in rows}

        output = {"clients": self.clients(subset),
                  "consultations": self.consultations(subset),
                  "referrals": self.referrals(subset),
                  "vulnerabilities": self.vulnerabilities(subset),
                  "themes": self.themes(subset),
                  "followups": self.followups(subset),
                  "efforts": self.efforts(subset),
                  }

        return output

    # -------------------------------------------------------------------------
    # Properties and helper functions
    # -------------------------------------------------------------------------
    @property
    def sector_id(self):
        """
            The record ID of the relevant sector (lazy property)

            Returns:
                org_sector record ID
        """

        sector_id = self._sector_id
        if sector_id is None:

            table = current.s3db.org_sector

            query = (table.abrv == self.sector) & (table.deleted == False)
            row = current.db(query).select(table.id, limitby=(0, 1)).first()

            sector_id = self._sector_id = row.id if row else None

        return sector_id

    # -------------------------------------------------------------------------
    @staticmethod
    def need_ids(code):
        """
            Returns a sub-select for dvr_need.id matching the given type code

            Args:
                code: the need type code

            Returns:
                sub-select
        """

        table = current.s3db.dvr_need
        if isinstance(code, (tuple, set, list)):
            query = (table.code.belongs(code))
        else:
            query = (table.code == code)
        query &= (table.deleted == False)

        return current.db(query)._select(table.id)

    # -------------------------------------------------------------------------
    def theme_ids(self, need=None, invert=False):
        """
            Returns a sub-select for the themes in the relevant sector

            Args:
                need: limit selection to themes linked to need types with
                      this type code(s)
                invert: invert the need filter

            Returns:
                sub-select
        """

        table = current.s3db.dvr_response_theme
        query = (table.sector_id == self.sector_id)
        if need:
            if invert:
                query &= (~(table.need_id.belongs(self.need_ids(need))))
            else:
                query &= (table.need_id.belongs(self.need_ids(need)))
        query &= (table.deleted == False)
        return current.db(query)._select(table.id)

    # -------------------------------------------------------------------------
    def action_ids(self, subset, need=None, invert=False):
        """
            Returns a sub-select for actions in the subset linked to relevant
            themes

            Args:
                subset: a pre-filtered set of dvr_response_action.id
                need: limit selection to actions with themes linked to need
                      types with this type code(s)
                invert: invert the need filter

            Returns:
                sub-select
        """

        table = current.s3db.dvr_response_action_theme
        query = (table.theme_id.belongs(self.theme_ids(need=need, invert=invert))) & \
                (table.action_id.belongs(subset)) & \
                (table.deleted == False)
        return current.db(query)._select(table.action_id, distinct=True)

    # -------------------------------------------------------------------------
    def dbset(self, subset, code=None, indirect_closure=False, need=None, invert=False):
        """
            Returns a Set (dbset) of relevant dvr_response_action

            Args:
                subset: a pre-filtered set of dvr_response_action.id
                code: limit selection to actions of types with this type code
                      (without a code, selection is limited to consultation types)
                indirect_closure: whether to include actions that have been
                                  accomplished by participation of the client
                                  in another action
                need: limit selection to actions with themes linked to needs
                      with this type code(s) (mutually exclusive with code)
                invert: invert the need filter

            Returns:
                a Set (dbset)
        """

        db = current.db
        s3db = current.s3db

        # Status filter
        stable = s3db.dvr_response_status
        query = (stable.is_closed == True)
        if not indirect_closure:
            query &= (stable.is_indirect_closure == False)
        query &= (stable.is_canceled == False) & \
                 (stable.deleted == False)
        status_ids = db(query)._select(stable.id)

        # Type filter
        ttable = s3db.dvr_response_type
        if code:
            query = (ttable.code == code)
        else:
            query = (ttable.is_consultation == True)
        query &= (ttable.deleted == False)
        type_ids = db(query)._select(ttable.id)

        # Themes filter
        if not code:
            subset = self.action_ids(subset, need=need, invert=invert)

        atable = s3db.dvr_response_action
        master_query = (atable.status_id.belongs(status_ids)) & \
                       (atable.response_type_id.belongs(type_ids)) & \
                       (atable.id.belongs(subset)) & \
                       (atable.deleted == False)

        return db(master_query)

    # -------------------------------------------------------------------------
    # Client indicators
    # -------------------------------------------------------------------------
    def clients(self, subset):
        """
            Indicators for clients

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 2 Anzahl der beratenen Personen
                + other client indicators
        """

        s3db = current.s3db
        atable = s3db.dvr_response_action

        # Include actions with indirect closure
        dbset = self.dbset(subset, indirect_closure=True)

        clients = {}

        num_clients = atable.person_id.count(distinct=True)
        row = dbset.select(num_clients).first()

        clients["total"] = row[num_clients]
        clients["gender"] = self.clients_by_gender(dbset)
        clients["age_group"] = self.clients_by_age_group(dbset)
        clients["nationality"] = self.clients_by_nationality(dbset)

        return clients

    # -------------------------------------------------------------------------
    @staticmethod
    def clients_by_gender(dbset):
        """
            Indicators for clients by gender

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 4 Anzahl aller Männer
                # 5 Anzahl aller Frauen
                # 6 Anzahl aller Divers
        """

        gender_groups = (("male", 3), ("female", 2), ("diverse", 4))

        s3db = current.s3db

        atable = s3db.dvr_response_action
        ptable = s3db.pr_person
        join = ptable.on(ptable.id == atable.person_id)

        num_clients = ptable.id.count(distinct=True)
        rows = dbset.select(num_clients,
                            ptable.gender,
                            join = join,
                            groupby = ptable.gender,
                            )
        clients = {}
        for row in rows:
            clients[row.pr_person.gender] = row[num_clients]

        return {k: clients.get(v, 0) for k, v in gender_groups}

    # -------------------------------------------------------------------------
    @staticmethod
    def clients_by_age_group(dbset):
        """
            Indicators for clients by age group

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 7 Anzahl aller Personen bis zum vollendeten 18. Lebensjahr
                # 8 Anzahl aller Personen vom vollendeten 18. bis zum vollendeten 27. Lebensjahr
                # 9 Anzahl aller Personen über dem vollendeten 65. Lebensjahr
        """

        age_groups = {(0, 18): 0, (18, 27): 0, (27, 65): 0, (65, None): 0}

        s3db = current.s3db

        atable = s3db.dvr_response_action
        ptable = s3db.pr_person
        join = ptable.on(ptable.id == atable.person_id)

        rows = dbset.select(atable.id,
                            atable.date,
                            ptable.date_of_birth,
                            join = join,
                            )
        for row in rows:
            action = row.dvr_response_action
            client = row.pr_person
            age = relativedelta(action.date, client.date_of_birth).years
            for g in age_groups:
                if age >= g[0] and (g[1] is None or age < g[1]):
                    age_groups[g] += 1

        return {"u18": age_groups[(0, 18)],
                "18-27": age_groups[(18, 27)],
                "65+": age_groups[(65, None)],
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def clients_by_nationality(dbset):
        """
            Indicators for clients by nationality

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 10 Anzahl aller beratenen Personen aus Syrien
                # 11 Anzahl aller beratenen Personen aus Afghanistan
                # 12 Anzahl aller beratenen Personen aus Türkei
                # 13 Anzahl aller beratenen Personen aus Georgien
                # 14 Anzahl aller beratenen Personen aus Iran
                # 15 Anzahl aller beratenen Personen aus Irak
                # 16 Anzahl aller beratenen Personen aus Russische Föderation
                # 17 Anzahl aller beratenen Personen aus Nordmazedonien
                # 18 Anzahl aller beratenen Personen aus Venezuela
                # 19 Anzahl aller beratenen Personen aus Somalia
                # 20 Anzahl aller beratenen Personen aus Eritrea
                # 21 Anzahl aller beratenen Personen aus Algerien
                # 22 Anzahl aller beratenen Personen aus Kolumbien
                # 23 Anzahl aller beratenen Personen aus Tunesien
                # 24 Anzahl aller beratenen Personen aus Nigeria
                # 25 Anzahl aller beratenen Personen aus Ungeklärt
                # 26 Anzahl aller beratenen Personen aus Indien
                # 27 Anzahl aller beratenen Personen aus Pakistan
                # 28 Anzahl aller beratenen Personen aus Ägypten
                # 29 Anzahl aller beratenen Personen aus Serbien
                # 30 Anzahl aller beratenen Personen aus anderen Staaten
        """

        nationalities = ("SY", "AF", "TR", "GE", "IR", "IQ", "RU",
                         "MK", "VE", "SO", "ER", "DZ", "CO", "TN",
                         "NG", None, "IN", "PK", "EG", "RS", "*"
                         )

        s3db = current.s3db

        atable = s3db.dvr_response_action
        dtable = s3db.pr_person_details
        left = dtable.on(dtable.person_id == atable.person_id)

        num_clients = atable.person_id.count(distinct=True)
        rows = dbset.select(num_clients,
                            dtable.nationality,
                            left = left,
                            groupby = dtable.nationality,
                            )
        clients = {n:0 for n in nationalities}
        for row in rows:
            nationality = row.pr_person_details.nationality
            if nationality not in nationalities:
                nationality = "*"
            clients[nationality] += 1

        return clients

    # -------------------------------------------------------------------------
    # Consultation indicators
    # -------------------------------------------------------------------------
    def consultations(self, subset):
        """
            Indicators for consultation totals

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 1 Anzahl der Beratungen
                # 3 Anzahl der Beratungen pro VZÄ (Durchschnitt)
        """

        s3db = current.s3db
        atable = s3db.dvr_response_action

        dbset = self.dbset(subset)

        num_actions = atable.id.count(distinct=True)
        row = dbset.select(num_actions).first()

        return {"total": row[num_actions], "per_fte": None}

    # -------------------------------------------------------------------------
    def referrals(self, subset):
        """
            Indicators for referrals

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 31 Anzahl der Fälle bei denen eine Weiterleitung zu Beratungsstelle stattgefunden hat
        """

        response_type = "REF"

        s3db = current.s3db
        atable = s3db.dvr_response_action

        dbset = self.dbset(subset, code=response_type)

        num_actions = atable.id.count(distinct=True)
        row = dbset.select(num_actions).first()

        return {"total": row[num_actions],
                }

    # -------------------------------------------------------------------------
    def followups(self, subset):
        """
            Indicators for initial consultations / followups

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 51 Anzahl der Erstgespräche (Erstes Beratungsgespräch eines Falles) gesamt
                # 52 Anzahl der Folgegespräche (Beratungen nach Erstberatung eines Falles) gesamt
        """

        response_types = {"INI": "initial", "FUP": "followup"}

        s3db = current.s3db
        atable = s3db.dvr_response_action

        result = {}
        for code, indicator in response_types.items():

            dbset = self.dbset(subset, code=code)
            num_actions = atable.id.count(distinct=True)

            row = dbset.select(num_actions).first()
            result[indicator] = row[num_actions] if row else 0

        return result

    # -------------------------------------------------------------------------
    def themes(self, subset):
        """
            Indicators for counseling reasons (by themes)

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 46 Anzahl der Beratungen mit dem Themenschwerpunkt Anhörung
                # 47 Anzahl der Beratungen mit dem Themenschwerpunkt Bescheid
                # 48 Anzahl der Beratungen mit dem Themenschwerpunkt Klage
                # 49 Anzahl der Beratungen mit dem Themenschwerpunkt Dublin
                # 50 Anzahl der Beratungen mit dem Themenschwerpunkt Sonstiges
        """

        needs = ("HEARING", "DECISION", "COMPLAINT", "DUBLIN")

        table = current.s3db.dvr_response_action
        num_actions = table.id.count()

        result = {}
        for need in needs:
            dbset = self.dbset(subset, need=need)
            row = dbset.select(num_actions).first()
            result[need] = row[num_actions] if row else 0

        dbset = self.dbset(subset, need=needs, invert=True)
        row = dbset.select(num_actions).first()
        result["*"] = row[num_actions] if row else 0

        return result

    # -------------------------------------------------------------------------
    # Vulnerabilities indicators
    # -------------------------------------------------------------------------
    def vulnerabilities(self, subset):
        """
            Indicators for vulnerability reports

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 32 Anzahl der Weiterleitung von Meldebögen zu Vulnerabilitäten an BAMF
                # 33 Davon Anzahl der Fälle zu unbegleiteten minderjährigen Ausländern
                # 34 Davon Anzahl der Fälle zu sexueller Orientierung oder geschlechtlicher Identität
                # 35 Davon Anzahl der Fälle zu Opfer von Menschenhandel
                # 36 Davon Anzahl der Falle infolge von Folter, Vergewaltigung oder sonstigen schweren Formen psychischer, physischer oder sexueller Gewalt
                # 37 Davon Anzahl der Fälle zu Behinderung
                # 38 Davon Anzahl der Fälle die keiner der oben genannten Kategorien zugewiesen werden kann
                # 39 Anzahl der Weiterleitung von Vulnerabilitäten an Aufnahmeeinrichtungen
                # 40 Davon Anzahl der Fälle zu unbegleiteten minderjährigen Ausländern
                # 41 Davon Anzahl der Fälle zu sexueller Orientierung oder geschlechtlicher identität
                # 42 Davon Anzahl der Fälle zu Opfer von Menschenhandel
                # 43 Davon Anzahl der Falle infolge von Folter, Vergewaltigung oder sonstigen schweren Formen psychischer, physischer oder sexueller Gewalt
                # 44 Davon Anzahl der Fälle zu Behinderung
                # 45 Davon Anzahl der Fälle die keiner der oben genannten Kategorien zugewiesen werden kann
        """

        response_types = ("VRBAMF", "VRRP")
        vulnerability_types = ("UAM", "LGBQTi", "VHT", "VT", "DISAB", "*")

        db = current.db
        s3db = current.s3db

        atable = s3db.dvr_response_action
        vtable = s3db.dvr_vulnerability
        ttable = s3db.dvr_vulnerability_type
        ltable = s3db.dvr_vulnerability_type_sector
        rtable = s3db.dvr_vulnerability_response_action

        reports = {}

        # All vulnerability types linked to self.sector
        query = (ltable.sector_id == self.sector_id) & \
                (ltable.deleted == False)
        type_ids = db(query)._select(ltable.vulnerability_type_id)

        query = (ttable.id.belongs(type_ids))
        rows = db(query).select(ttable.id, ttable.code)
        types = {row.id: row.code for row in rows}

        for code in response_types:
            dbset = self.dbset(subset, code=code)

            # Count all reports
            num_reports = atable.id.count(distinct=True)
            row = dbset.select(num_reports).first()
            output = {"reports": row[num_reports] if row else 0}

            # Count cases per vulnerability type
            # - where vulnerability is linked to the report
            join = [rtable.on((rtable.action_id == atable.id) & \
                              (rtable.deleted == False)),
                    vtable.on((vtable.id == rtable.vulnerability_id) & \
                              (vtable.person_id == atable.person_id) & \
                              (vtable.vulnerability_type_id.belongs(type_ids)) & \
                              (vtable.deleted == False)),
                    ]
            # Alternative join (if direct vulnerability<=>action links not available)
            # - where the vulnerability applied at the same time as the report
            #join = vtable.on((vtable.person_id == atable.person_id) & \
                             #(vtable.vulnerability_type_id.belongs(type_ids)) & \
                             #((vtable.date == None) | (vtable.date <= atable.start_date)) & \
                             #((vtable.end_date == None) | (vtable.end_date >= atable.start_date)) & \
                             #(vtable.deleted == False))
            type_id = vtable.vulnerability_type_id
            num_clients = vtable.person_id.count(distinct=True)
            rows = dbset.select(num_clients, type_id, join=join, groupby=type_id)

            # Sort by required vulnerability types
            cases = {k: 0 for k in vulnerability_types}
            for row in rows:
                vcode = types.get(row[type_id])
                if vcode not in cases:
                    vcode = "*"
                cases[vcode] += row[num_clients]
            output["cases"] = cases

            reports[code] = output

        return reports

    # -------------------------------------------------------------------------
    # Efforts indicators
    # -------------------------------------------------------------------------
    def efforts(self, subset):
        """
            Indicators for efforts

            Args:
                subset: the dvr_response_action subset (list of record IDs)

            Returns:
                indicator dict

            Indicators:
                # 53 Anzahl der Beratungen mit einer Beratungszeit unter 15 Minuten
                # 54 Anzahl der Beratungen mit einer Beratungszeit unter 30 Minuten
                # 55 Anzahl der Beratungen mit einer Beratungszeit unter 60 Minuten
        """

        db = current.db
        s3db = current.s3db

        atable = s3db.dvr_response_action
        ltable = s3db.dvr_response_action_theme

        dbset = self.dbset(subset)
        action_ids = dbset._select(atable.id)
        theme_ids = self.theme_ids()

        # All actions with any efforts recorded per-theme
        query = (ltable.action_id.belongs(action_ids)) & \
                (ltable.hours != None) & \
                (ltable.deleted == False)
        actions_with_theme_efforts = db(query)._select(ltable.action_id)

        # For these actions, compute the total effort for sector-related themes
        query = (ltable.action_id.belongs(actions_with_theme_efforts)) & \
                (ltable.theme_id.belongs(theme_ids)) & \
                (ltable.deleted == False)
        action_id = ltable.action_id
        total_hours = ltable.hours.sum()
        rows = db(query).select(action_id,
                                total_hours,
                                groupby = action_id,
                                )
        efforts = {row[action_id]: row[total_hours] for row in rows}

        # For all other actions in the set...
        query = ~atable.id.belongs(efforts.keys())

        # ...determine the total effort and the total number of theme links
        left = ltable.on((ltable.action_id == atable.id) & \
                         (ltable.deleted == False))
        action_id = atable.id
        total_hours = atable.hours.max()
        num_links = ltable.id.count()
        rows = dbset(query).select(action_id,
                                   total_hours,
                                   num_links,
                                   left = left,
                                   groupby = action_id,
                                   )

        # ...compute average per-theme effort per action
        per_theme_efforts = {}
        for row in rows:
            record_id = row[action_id]
            hours = row[total_hours]
            links = row[num_links]
            per_theme_efforts[record_id] = hours / links if links else 0

        # ...determine the number of links to sector-related themes per action
        left = ltable.on((ltable.action_id == atable.id) & \
                         (ltable.theme_id.belongs(theme_ids)) & \
                         (ltable.deleted == False))
        rows = dbset(query).select(action_id,
                                   num_links,
                                   left = left,
                                   groupby = action_id,
                                   having = num_links > 0,
                                   )

        # From this, calculate an estimate for the total effort
        # for sector-related themes per action
        for row in rows:
            record_id = row[action_id]
            if record_id not in efforts:
                efforts[record_id] = per_theme_efforts.get(record_id, 0) * row[num_links]

        # Count actions per effort limit group
        groups = (("<15min", 0.25), ("<30min", 0.5), ("<60min", 1.0))
        result = {k: 0 for k, _ in groups}
        for record_id, hours in efforts.items():
            for indicator, limit in groups:
                if hours < limit:
                    result[indicator] += 1
                    # TODO assuming exclusive effort groups here
                    #      - but is this correct? (indicator definitions are insufficient)
                    break

        return result

    # -------------------------------------------------------------------------
    def export(self, resource, sheet, title, subtitle=None):
        """
            Export performance indicators

            Args:
                resource: the CRUDResource
                sheet: the XLS worksheet to write to
                title: the title for the export
                subtitle: an optional subtitle (e.g. start+end dates)
        """

        T = current.T
        s3db = current.s3db

        indicators = self.compute(resource)

        write = self.write
        rowindex = 0

        # Title
        write(sheet, rowindex, 0, title, style="header")
        rowindex += 1

        # Subtitle (optional)
        if subtitle:
            write(sheet, rowindex, 0, subtitle)
            rowindex += 2
        else:
            rowindex += 1

# =============================================================================
class PerformanceIndicatorExport(CRUDMethod):
    """ REST Method to produce a response statistics data sheet """

    # Custom Performance Indicator Sets
    PISETS = {"lea": PerformanceIndicatorsLEA,
              "bamf": PerformanceIndicatorsBAMF,
              }

    def __init__(self, pitype=None):
        """
            Args:
                pitype: the performance indicator set
        """

        super().__init__()

        indicators = self.PISETS.get(pitype) if pitype else None

        if indicators:
            self.indicators = indicators()
        else:
            # Default Set
            self.indicators = PerformanceIndicators()

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        output = {}

        if r.http == "GET":
            if r.representation == "xls":
                output = self.xls(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def xls(self, r, **attr):
        """
            Export the performance indicators as XLS data sheet

            Args:
                r: the CRUDRequest instance
                attr: controller attributes
        """

        try:
            import xlwt
        except ImportError as e:
            raise HTTP(503, body="XLWT not installed") from e

        T = current.T
        resource = self.resource
        table = resource.table

        # Get the statistics
        indicators = self.indicators

        # Create workbook and sheet
        book = xlwt.Workbook(encoding="utf-8")

        title = s3_str(T("Performance Indicators"))
        sheet = book.add_sheet(title)

        # Title and Report Dates (from filter)
        dates = []
        get_vars = r.get_vars
        field = table.date
        for fvar in ("~.start_date__ge", "~.end_date__le"):
            dtstr = get_vars.get(fvar)
            if dtstr:
                try:
                    dt = s3_decode_iso_datetime(dtstr).date()
                except (ValueError, AttributeError):
                    dt = None
                else:
                    dates.append(field.represent(dt))
            else:
                dates.append("...")
        dates = " -- ".join(dates) if dates else None

        # Write the performance indicators
        indicators.export(resource, sheet, title, subtitle=dates)

        # Output
        output = BytesIO()
        book.save(output)
        output.seek(0)

        # Response headers
        from gluon.contenttype import contenttype
        disposition = "attachment; filename=\"%s\"" % "indicators.xls"
        response = current.response
        response.headers["Content-Type"] = contenttype(".xls")
        response.headers["Content-disposition"] = disposition

        from gluon.streamer import DEFAULT_CHUNK_SIZE
        return response.stream(output,
                               chunk_size=DEFAULT_CHUNK_SIZE,
                               request=r,
                               )

# END =========================================================================
