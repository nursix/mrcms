# Database upgrade script
#
# MRCMS Template Version 1.7.1 => 1.7.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.7.1-1.7.2.py
#
import sys
import datetime

#from core import S3Duplicate

# Override auth (disables all permission checks)
auth.override = True

# Initialize failed-flag
failed = False

# Info
def info(msg):
    sys.stderr.write("%s" % msg)
    sys.stderr.flush()
def infoln(msg):
    sys.stderr.write("%s\n" % msg)
    sys.stderr.flush()

# Load models for tables
ntable = s3db.dvr_need
ttable = s3db.dvr_response_theme
ltable = s3db.dvr_response_action_theme
stable = s3db.org_sector
atable = s3db.dvr_case_activity

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Rename needs
#
if not failed:
    info("Rename needs...")

    rename = {"Unterstützung von Anerkannten": "Behördenangelegenheiten",
              "Familieneinheit": "Familie/Partnerschaft",
              "Strafverfahren/Bußgeldbescheide": "Rechtliches",
              "Taschengeld": "Finanzielles",
              "Unterbringungssituation": "Unterbringung",
              "Gesundheitsbedarfe": "Gesundheit",
              "Deeskalation": "Konflikte",
              }

    query = ntable.name.belongs(rename.keys())
    rows = db(query).select(ntable.id, ntable.name)

    needs = {row.name: row for row in rows}
    updated, missing = 0, 0
    for old, new in rename.items():
        row = needs.get(old)
        if not row:
            info("-")
            missing += 1
            continue
        row.update_record(name=new,
                          modified_by=ntable.modified_by,
                          modified_on=ntable.modified_on,
                          )
        info(".")
        updated += 1

    infoln("...done (%s need types renamed, %s not found)" % (updated, missing))

# -----------------------------------------------------------------------------
# Rename themes
#
if not failed:
    info("Rename themes...")

    rename = {"Jobcenter": "Agentur für Arbeit",
              "Vaterschaftsanerkennung/Sorgeerklärung": "Vaterschaftsanerkennung",
              "Getrennte Familie": "Trennung",
              "Sonstigen Rechnungen": "Verpflichtungen/Schulden",
              "Taschengeld nicht erhalten": "Leistungen",
              "Beschlagnahmung von Bargeld": "Einkommen/Vermögen",
              "Bankkonto Antrag": "Bank",
              "Strafverfahren: allgemeines Strafrecht": "Strafverfahren",
              "Deeskalation": "Andere Konflikte",
              "Beschulung Regelschule": "Beschulung Regelschule / weiterführende Schulen",
              }

    query = ttable.name.belongs(rename.keys())
    rows = db(query).select(ttable.id, ttable.name)

    themes = {row.name: row for row in rows}
    updated, missing = 0, 0
    for old, new in rename.items():
        row = themes.get(old)
        if not row:
            info("-")
            missing += 1
            continue
        row.update_record(name=new,
                          modified_by=ttable.modified_by,
                          modified_on=ttable.modified_on,
                          )
        info(".")
        updated += 1

    infoln("...done (%s themes renamed, %s not found)" % (updated, missing))

# -----------------------------------------------------------------------------
# Change theme sectors
#
if not failed:
    info("Change theme sectors...")

    change = {"Info bei Anerkennung": "Asylverfahrensberatung",
              "Agentur für Arbeit": "Sozialberatung",
              "Krankenkasse": "Sozialberatung",
              "Trennung": "Sozialberatung",
              "Vaterschaftsanerkennung": "Sozialberatung",
              "Identifizierungsbogen": "Sozialberatung",
              "PROTECT": "Sozialberatung",
              }

    # Look up sector IDs
    query = stable.name.belongs(set(change.values()))
    rows = db(query).select(stable.id, stable.name)
    sectors = {row.name: row.id for row in rows}

    # Change sector_ids
    query = ttable.name.belongs(change.keys())
    rows = db(query).select(ttable.id, ttable.name, ttable.sector_id)

    themes = {row.name: row for row in rows}
    updated, missing, invalid = 0, 0, 0
    for theme, sector in change.items():
        sector_id = sectors.get(sector)
        if not sector_id:
            info("?")
            invalid += 1
            continue
        row = themes.get(theme)
        if not row:
            info("-")
            missing += 1
            continue
        row.update_record(sector_id=sector_id,
                          modified_by=ttable.modified_by,
                          modified_on=ttable.modified_on,
                          )
        info(".")
        updated += 1

    infoln("...done (%s themes updated, %s not found, %s invalid sectors)" % (updated, missing, invalid))

# -----------------------------------------------------------------------------
# Change theme need type
#
if not failed:
    info("Change theme need types...")

    activity_ids = set()

    change = {"Folter, psychische, physische oder sexuelle Gewalt": "Psychosoziales",
              "Verpflichtungen/Schulden": "Finanzielles",
              "Info bei Anerkennung": "Allgemeine Infos zum Asylverfahren",
              "Krankenkasse": "Gesundheit",
              }

    # Look up need_ids
    query = (ntable.name.belongs(set(change.values()))) & \
            (ntable.deleted == False)
    rows = db(query).select(ntable.id, ntable.name)
    needs = {row.name: row.id for row in rows}

    # Look up the themes
    query = (ttable.name.belongs(change.keys())) & \
            (ttable.deleted == False)
    rows = db(query).select(ttable.id, ttable.name)
    themes = {row.name: row for row in rows}

    updated, missing, linked = 0, 0, 0
    for theme, need in change.items():
        # Change the need type of the theme
        row = themes.get(theme)
        need_id = needs.get(need)
        if row and need_id:
            row.update_record(need_id = need_id,
                              modified_by = ttable.modified_by,
                              modified_on = ttable.modified_on,
                              )
        else:
            info("?")
            missing += 1
            continue

        # Look up all dvr_response_action_theme with this theme
        # - run onaccept to re-link to case activities with the correct need_id
        query = (ltable.theme_id == row.id) & \
                (ltable.deleted == False)
        details = db(query).select(ltable.id,
                                   ltable.case_activity_id,
                                   )
        for item in details:
            activity_ids.add(item.case_activity_id)
            s3db.onaccept(ltable, {"id": item.id}, method="update")
            linked += 1

        info(".")
        updated += 1

    infoln("...done (%s themes updated, %s not found, %s measures fixed)" % (updated, missing, linked))

# -----------------------------------------------------------------------------
# Replace themes
#
if not failed:
    info("Replace themes...")

    replace = {"Ermittlungsverfahren": "Strafverfahren",
               "Fahrpreisnacherhebung": "Strafverfahren",
               "Ordnungswidrigkeit": "Strafverfahren",
               "Strafverfahren: Ausländerrecht": "Strafverfahren",
               "Einstellungsbescheid Leistungen": "Leistungen",
               "Sonstiges": "Leistungen",
               "Allgemeine Infos": "Unterbringungssituation",
               "Beschlagnahmungen": "Unterbringungssituation",
               "Dolmetscherkoordination": "Unterbringungssituation",
               }

    names = set(replace.keys()) | set(replace.values())

    query = (ttable.name.belongs(names)) & \
            (ttable.deleted == False)
    rows = db(query).select(ttable.id, ttable.name)
    themes = {row.name: row.id for row in rows}

    replace_ids = {themes[k]: themes[v] for k, v in replace.items()}

    query = (ltable.theme_id.belongs(replace_ids.keys())) & \
            (ltable.deleted == False)
    details = db(query).select(ltable.id,
                               ltable.case_activity_id,
                               ltable.theme_id,
                               )

    updated = 0
    for item in details:
        theme_id = replace_ids.get(item.theme_id)
        if theme_id:
            item.update_record(theme_id = theme_id,
                               modified_on = ltable.modified_on,
                               modified_by = ltable.modified_by,
                               )
            s3db.onaccept(ltable, item, method="update")
            info(".")
            updated += 1
        else:
            info("-")

    infoln("...done (%s measures updated)" % updated)

# -----------------------------------------------------------------------------

if not failed:
    info("Remove obsolete case activities")

    if activity_ids:
        # Remove all case activities these details were previously linked to
        # and which are now no longer linked to any response actions
        left = ltable.on(ltable.case_activity_id == atable.id)
        query = atable.id.belongs(activity_ids) & \
                (ltable.id == None) & \
                ((atable.need_details == "") | (atable.need_details == None)) & \
                ((atable.outcome == "") | (atable.outcome == None))
        empty = db(query).select(atable.id, left=left)
        activity_ids = [activity.id for activity in empty]

        resource = s3db.resource("dvr_case_activity", id=activity_ids)
        deleted = resource.delete(cascade=True)

        infoln("...done (%s activities deleted)" % deleted)
    else:
        infoln("...not required")

# -----------------------------------------------------------------------------
# Remove obsolete themes
#
if not failed:
    info("Remove obsolete themes")

    obsolete = {"Ermittlungsverfahren",
                "Fahrpreisnacherhebung",
                "Ordnungswidrigkeit",
                "Strafverfahren: Ausländerrecht",
                "Einstellungsbescheid Leistungen",
                "Sonstiges",
                "Allgemeine Infos",
                "Beschlagnahmungen",
                "Dolmetscherkoordination",
                }

    query = (ttable.name.belongs(obsolete)) & \
            (ttable.deleted == False)
    themes = db(query).select(ttable.id)

    resource = s3db.resource("dvr_response_theme", id=[t.id for t in themes])
    deleted = resource.delete(cascade=True)
    if deleted == len(themes):
        infoln("...done (%s themes removed)" % deleted)
    else:
        infoln("...failed")

# -----------------------------------------------------------------------------
# Remove obsolete need types
#
if not failed:
    info("Remove obsolete need types")

    obsolete = {"Gewalterfahrung",
                "Versorgung/Angebote in der Einrichtung",
                }

    query = (ntable.name.belongs(obsolete)) & \
            (ntable.deleted == False)
    needs = db(query).select(ntable.id)
    need_ids = {n.id for n in needs}

    # Remove all case activities linked to these needs
    query = (atable.need_id.belongs(need_ids)) & \
            (atable.deleted == False)
    activities = db(query).select(atable.id)

    resource = s3db.resource("dvr_case_activity", id=[a.id for a in activities])
    resource.delete(cascade=True)

    # Remove the need types
    resource = s3db.resource("dvr_need", id=list(need_ids))
    deleted = resource.delete(cascade=True)
    if deleted == len(needs):
        infoln("...done (%s need types removed)" % deleted)
    else:
        infoln("...failed")
        failed = True

# -----------------------------------------------------------------------------
# Import new need types
#
if not failed:
    info("Import new need types")

    resource = s3db.resource("dvr_need")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "need.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "upgrade", "dvr_need_1.7.2.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Import new themes
#
if not failed:
    info("Import new themes")


    resource = s3db.resource("dvr_response_theme")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_theme.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "upgrade", "dvr_response_theme_1.7.2.csv")

    # Import, capture errors
    try:
        with open(filename, "r") as File:
            resource.import_xml(File, source_type="csv", stylesheet=stylesheet)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
    else:
        error = resource.error

    # Fail on any error
    if error:
        infoln("...failed")
        infoln(error)
        failed = True
    else:
        infoln("...done")

# -----------------------------------------------------------------------------
# Finishing up
#
if failed:
    db.rollback()
    infoln("UPGRADE FAILED - Action rolled back.")
else:
    db.commit()
    infoln("UPGRADE SUCCESSFUL.")

# END =========================================================================
