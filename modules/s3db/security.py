"""
    Security Model

    Copyright: 2012-2022 (c) Sahana Software Foundation

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("SecurityZonesModel",
           "SecuritySeizedItemsModel",
           )

from gluon import *
from gluon.storage import Storage
from ..core import *
from core.ui.layouts import PopupLink

# =============================================================================
class SecurityZonesModel(DataModel):
    """ Model for security zones """

    names = ("security_level",
             "security_zone_type",
             "security_zone",
             "security_staff_type",
             "security_staff",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        location_id = self.gis_location_id

        # -----------------------------------------------------------
        # Security Levels
        # - according to the UN Security Level System (SLS)
        # http://ictemergency.wfp.org/c/document_library/get_file?uuid=c025cb98-2297-4208-bcc6-76ba02719c02&groupId=10844
        # http://geonode.wfp.org/layers/geonode:wld_bnd_securitylevel_wfp
        #

        level_opts = {1: T("Minimal"),
                      2: T("Low"),
                      3: T("Moderate"),
                      4: T("Substantial"),
                      5: T("High"),
                      6: T("Extreme"),
                      }

        tablename = "security_level"
        define_table(tablename,
                     location_id(
                        #label = T("Security Level Area"),
                        widget = LocationSelector(show_map = False),
                        ),
                     # Overall Level
                     Field("level", "integer",
                           label = T("Security Level"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     # Categories
                     Field("armed_conflict", "integer",
                           label = T("Armed Conflict"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("terrorism", "integer",
                           label = T("Terrorism"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("crime", "integer",
                           label = T("Crime"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("civil_unrest", "integer",
                           label = T("Civil Unrest"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           ),
                     Field("hazards", "integer",
                           label = T("Hazards"),
                           represent = lambda v: level_opts.get(v,
                                                current.messages.UNKNOWN_OPT),
                           requires = IS_IN_SET(level_opts),
                           comment = T("e.g. earthquakes or floods"),
                           ),
                     CommentsField(),
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Classify Area"),
            title_display = T("Security Level Details"),
            title_list = T("Security Levels"),
            title_update = T("Edit Security Level"),
            title_upload = T("Import Security Levels"),
            label_list_button = T("List Security Levels"),
            label_delete_button = T("Delete Security Level"),
            msg_record_created = T("Security Area classified"),
            msg_record_modified = T("Security Level updated"),
            msg_record_deleted = T("Security Level deleted"),
            msg_list_empty = T("No Security Areas currently classified"))

        # -----------------------------------------------------------
        # Security Zone Types
        #
        tablename = "security_zone_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     CommentsField(),
                     )

        # CRUD strings
        ADD_ZONE_TYPE = T("Create Zone Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE_TYPE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_upload = T("Import Zone Types"),
            label_list_button = T("List Zone Types"),
            label_delete_button = T("Delete Zone Type"),
            msg_record_created = T("Zone Type added"),
            msg_record_modified = T("Zone Type updated"),
            msg_record_deleted = T("Zone Type deleted"),
            msg_list_empty = T("No Zone Types currently registered"))

        zone_type_represent = S3Represent(lookup=tablename)

        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        # -----------------------------------------------------------
        # Security Zones
        #
        tablename = "security_zone"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     Field("zone_type_id", db.security_zone_type,
                           label = T("Type"),
                           represent = zone_type_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_zone_type.id",
                                                  zone_type_represent,
                                                  sort=True)),
                           comment = PopupLink(c = "security",
                                               f = "zone_type",
                                               label = ADD_ZONE_TYPE,
                                               tooltip = T("Select a Zone Type from the list or click 'Add Zone Type'"),
                                               ),
                           ),
                     location_id(
                        widget = LocationSelector(catalog_layers = True,
                                                  points = False,
                                                  polygons = True,
                                                  ),
                     ),
                     CommentsField(),
                     )

        # CRUD strings
        ADD_ZONE = T("Create Zone")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE,
            title_display = T("Zone Details"),
            title_list = T("Zones"),
            title_update = T("Edit Zone"),
            title_upload = T("Import Zones"),
            label_list_button = T("List Zones"),
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        zone_represent = S3Represent(lookup=tablename)

        # -----------------------------------------------------------
        # Security Staff Types
        #
        tablename = "security_staff_type"
        define_table(tablename,
                     Field("name",
                           label=T("Name")),
                     CommentsField(),
                     )

        # CRUD strings
        ADD_STAFF = T("Add Staff Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_STAFF,
            title_display = T("Staff Type Details"),
            title_list = T("Staff Types"),
            title_update = T("Edit Staff Type"),
            title_upload = T("Import Staff Types"),
            label_list_button = T("List Staff Types"),
            label_delete_button = T("Delete Staff Type"),
            msg_record_created = T("Staff Type added"),
            msg_record_modified = T("Staff Type updated"),
            msg_record_deleted = T("Staff Type deleted"),
            msg_list_empty = T("No Staff Types currently registered"))

        staff_type_represent = S3Represent(lookup=tablename)

        # -----------------------------------------------------------
        # Security Staff
        #
        tablename = "security_staff"
        define_table(tablename,
                     self.hrm_human_resource_id(),
                     Field("staff_type_id", "list:reference security_staff_type",
                           label = T("Type"),
                           represent = self.security_staff_type_multirepresent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_staff_type.id",
                                                  staff_type_represent,
                                                  sort=True,
                                                  multiple=True)),
                           comment = PopupLink(c = "security",
                                               f = "staff_type",
                                               label = ADD_STAFF,
                                               tooltip = T("Select a Staff Type from the list or click 'Add Staff Type'"),
                                               ),
                           ),
                     Field("zone_id", db.security_zone,
                           label = T("Zone"),
                           represent = zone_represent,
                           requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "security_zone.id",
                                                  zone_represent,
                                                  sort=True)),
                           comment = PopupLink(c = "security",
                                               f = "zone",
                                               label = ADD_ZONE,
                                               tooltip = T("For wardens, select a Zone from the list or click 'Add Zone'"),
                                               ),
                           ),
                     self.super_link("site_id", "org_site",
                                     label = T("Facility"),
                                     represent = self.org_site_represent,
                                     readable = True,
                                     writable = True,
                                     ),
                     CommentsField(),
                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Add Security-Related Staff"),
            title_display = T("Security-Related Staff Details"),
            title_list = T("Security-Related Staff"),
            title_update = T("Edit Security-Related Staff"),
            title_upload = T("Import Security-Related Staff"),
            label_list_button = T("List Security-Related Staff"),
            label_delete_button = T("Delete Security-Related Staff"),
            msg_record_created = T("Security-Related Staff added"),
            msg_record_modified = T("Security-Related Staff updated"),
            msg_record_deleted = T("Security-Related Staff deleted"),
            msg_list_empty = T("No Security-Related Staff currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return None

    # -----------------------------------------------------------------------------
    @staticmethod
    def security_staff_type_multirepresent(opt):
        """ Represent a staff type in list views """

        db = current.db
        table = db.security_staff_type
        names = db(table.id > 0).select(table.id,
                                        table.name,
                                        ).as_dict()

        if isinstance(opt, (list, tuple)):
            opts = opt
            vals = [str(names.get(o)["name"]) for o in opts]
            multiple = True
        elif isinstance(opt, int):
            opts = [opt]
            vals = str(names.get(opt)["name"])
            multiple = False
        else:
            try:
                opt = int(opt)
            except (ValueError, TypeError):
                return current.messages["NONE"]
            else:
                opts = [opt]
                vals = str(names.get(opt)["name"])
                multiple = False

        if multiple:
            if len(opts) > 1:
                vals = ", ".join(vals)
            else:
                vals = vals[0] if vals else ""
        return vals

# =============================================================================
class SecuritySeizedItemsModel(DataModel):
    """
        Model for the tracking of seized items (e.g. in connection
        with security procedures at shelters, borders or transport
        hubs)
    """

    names = ("security_seized_item_type",
             "security_seized_item_depository",
             "security_seized_item",
             "security_seized_item_status_opts",
             )

    def model(self):

        T = current.T

        db = current.db
        s3 = current.response.s3

        crud_strings = s3.crud_strings

        define_table = self.define_table
        configure = self.configure

        person_id = self.pr_person_id

        # ---------------------------------------------------------------------
        # Seized Item Types
        #
        tablename = "security_seized_item_type"
        define_table(tablename,
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     CommentsField(),
                     )

        # Table Configuration
        configure(tablename,
                  deduplicate = S3Duplicate(),
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Item Type"),
            title_display = T("Item Type Details"),
            title_list = T("Item Types"),
            title_update = T("Edit Item Type"),
            label_list_button = T("List Item Types"),
            label_delete_button = T("Delete Item Type"),
            msg_record_created = T("Item Type created"),
            msg_record_modified = T("Item Type updated"),
            msg_record_deleted = T("Item Type deleted"),
            msg_list_empty = T("No Item Types currently defined"),
        )

        # Foreign Key Template
        represent = S3Represent(lookup=tablename, translate=True)
        item_type_id = FieldTemplate("item_type_id", "reference %s" % tablename,
                                     label = T("Type"),
                                     represent = represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                     sortby = "name",
                                     comment = PopupLink(c = "security",
                                                         f = "seized_item_type",
                                                         tooltip = T("Create new item type"),
                                                         ),
                                     )

        # ---------------------------------------------------------------------
        # Depositories
        #
        tablename = "security_seized_item_depository"
        define_table(tablename,
                     self.org_organisation_id(
                         default = None,
                         # Enable in template as required
                         readable = False,
                         writable = False,
                         ),
                     Field("name",
                           requires = IS_NOT_EMPTY(),
                           ),
                     CommentsField(),
                     )

        # Components
        self.add_components(tablename,
                            security_seized_item = "depository_id",
                            )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Depository"),
            title_display = T("Depository Details"),
            title_list = T("Depositories"),
            title_update = T("Edit Depository"),
            label_list_button = T("List Depositories"),
            label_delete_button = T("Delete Depository"),
            msg_record_created = T("Depository created"),
            msg_record_modified = T("Depository updated"),
            msg_record_deleted = T("Depository deleted"),
            msg_list_empty = T("No Depositories currently registered"),
            )

        # Foreign Key Template
        represent = S3Represent(lookup=tablename)
        depository_id = FieldTemplate("depository_id", "reference %s" % tablename,
                                      label = T("Depository"),
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "%s.id" % tablename,
                                                              represent,
                                                              )),
                                      sortby = "name",
                                      )

        # ---------------------------------------------------------------------
        # Seized Items
        #
        seized_item_status = {"DEP": T("deposited"),
                              "RET": T("returned to owner"),
                              "DIS": T("disposed of/destroyed"),
                              "FWD": T("forwarded"),
                              #"OTH": T("other"),
                              }
        tablename = "security_seized_item"
        define_table(tablename,
                     self.super_link("doc_id", "doc_entity"),
                     # Owner
                     person_id(empty = False,
                               label = T("Owner"),
                               ondelete = "CASCADE",
                               # Autocomplete using security controller
                               widget = S3PersonAutocompleteWidget(
                                           controller = "security",
                                           function = "person_search",
                                           ),
                               comment = None,
                               ),
                     # Type and number of items
                     item_type_id(empty = False,
                                  ondelete = "RESTRICT",
                                  ),
                     Field("number", "integer",
                           label = T("Count"),
                           requires = IS_INT_IN_RANGE(1, None),
                           ),
                     # Confiscated when and by whom
                     DateField(default = "now",
                               label = T("Confiscated on"),
                               ),
                     person_id("confiscated_by",
                               label = T("Confiscated by"),
                               default = current.auth.s3_logged_in_person(),
                               comment = None,
                               ),
                     # Status
                     Field("status",
                           default = "DEP",
                           requires = IS_IN_SET(seized_item_status, zero=None),
                           represent = represent_option(seized_item_status),
                           ),
                     depository_id(ondelete="SET NULL",
                                   ),
                     Field("status_comment",
                           label = T("Status Comment"),
                           represent = lambda v, row=None: v if v else "-",
                           ),
                     # Returned-date and person responsible
                     DateField("returned_on",
                               label = T("Returned on"),
                               # Set onaccept when returned=True
                               writable = False,
                               ),
                     person_id("returned_by",
                               label = T("Returned by"),
                               # Set onaccept when returned=True
                               writable = False,
                               comment = None,
                               ),
                     CommentsField(),
                     )

        # Filter Widgets
        filter_widgets = [TextFilter(["person_id$pe_label",
                                      "person_id$first_name",
                                      "person_id$middle_name",
                                      "person_id$last_name",
                                      "status_comment",
                                      "comments",
                                      ],
                                     label = T("Search"),
                                     ),
                          OptionsFilter("item_type_id",
                                        options = lambda: \
                                                  get_filter_options("security_seized_item_type"),
                                        ),
                          OptionsFilter("status",
                                        options = seized_item_status,
                                        cols = 2,
                                        default = "DEP",
                                        ),
                          OptionsFilter("depository_id",
                                        options = lambda: \
                                                  get_filter_options("security_seized_item_depository"),
                                        ),
                          DateFilter("date",
                                     hidden = True,
                                     ),
                          ]

        # List Fields
        list_fields = ("person_id",
                       "date",
                       "number",
                       "item_type_id",
                       #"confiscated_by",
                       "status",
                       "depository_id",
                       #"returned_on",
                       #"returned_by",
                       "comments",
                       )

        # Table Configuration
        configure(tablename,
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  onaccept = self.seized_item_onaccept,
                  orderby = "%s.date desc" % tablename,
                  super_entity = "doc_entity",
                  )

        # CRUD Strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Seized Item"),
            title_display = T("Seized Item Details"),
            title_list = T("Seized Items"),
            title_update = T("Edit Seized Item"),
            label_list_button = T("List Seized Items"),
            label_delete_button = T("Delete Seized Item"),
            msg_record_created = T("Seized Item created"),
            msg_record_modified = T("Seized Item updated"),
            msg_record_deleted = T("Seized Item deleted"),
            msg_list_empty = T("No Seized Items currently registered"),
        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"security_seized_item_status_opts": seized_item_status,
                }

    # -------------------------------------------------------------------------
    def defaults(self):
        """ Safe defaults for names in case the module is disabled """

        return {"security_seized_item_status_opts": {},
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def seized_item_onaccept(form):
        """
            Onaccept-routine for seized items:
                - set returned_on and returned_by if status=="RET"
        """

        db = current.db
        s3db = current.s3db

        # Get record ID
        formvars = form.vars
        try:
            record_id = formvars.id
        except AttributeError:
            return

        # Get record
        table = s3db.security_seized_item
        query = (table.id == record_id) & \
                (table.deleted == False)
        record = db(query).select(table.id,
                                  table.status,
                                  table.returned_on,
                                  table.returned_by,
                                  limitby = (0, 1),
                                  ).first()

        if not record:
            return

        if record.status == "RET":
            if not record.returned_on and not record.returned_by:
                now = current.request.utcnow.date()
                logged_in_person = current.auth.s3_logged_in_person()
                record.update_record(returned_on = now,
                                     returned_by = logged_in_person,
                                     )
        else:
            record.update_record(returned_on = None,
                                 returned_by = None,
                                 )

# END =========================================================================
