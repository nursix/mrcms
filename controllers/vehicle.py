"""
    Vehicle Management Functionality
"""

module = request.controller

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

# Vehicle Module depends on Assets
if not settings.has_module("asset"):
    raise HTTP(404, body="Module disabled: %s" % "asset")

# -----------------------------------------------------------------------------
def index():
    """ Module Home Page """

    module_name = settings.modules[module].get("name_nice")
    response.title = module_name

    return {"module_name": module_name,
            }

# -----------------------------------------------------------------------------
def create():
    """ Redirect to vehicle/create """
    redirect(URL(f="vehicle", args="create"))

# -----------------------------------------------------------------------------
def vehicle():
    """
        RESTful CRUD controller
        Filtered version of the asset_asset resource
    """

    tablename = "asset_asset"
    table = s3db[tablename]

    s3db.configure("vehicle_vehicle",
                   deletable = False,
                   )

    set_method = s3db.set_method

    set_method("asset_asset", method="assign",
               action = s3db.hrm_AssignMethod(component="human_resource"))

    set_method("asset_asset", method="check-in",
               action = s3base.S3CheckInMethod())

    set_method("asset_asset", method="check-out",
               action = s3base.S3CheckOutMethod())

    # Type is Vehicle
    VEHICLE = s3db.asset_types["VEHICLE"]
    field = table.type
    field.default = VEHICLE
    field.readable = False
    field.writable = False

    # Only show vehicles
    s3.filter = (field == VEHICLE)

    # Remove type from list_fields
    list_fields = s3db.get_config("asset_asset", "list_fields")
    if "type" in list_fields:
        list_fields.remove("type")

    field = table.item_id
    field.label = T("Vehicle Type")
    field.comment = PopupLink(f="item",
                              # Use this controller for options.json rather than looking for one called 'asset'
                              vars=dict(parent="vehicle"),
                              label=T("Add Vehicle Type"),
                              info=T("Add a new vehicle type"),
                              title=T("Vehicle Type"),
                              tooltip=T("Only Items whose Category are of type 'Vehicle' will be seen in the dropdown."))

    # Use this controller for options.json rather than looking for one called 'asset'
    table.organisation_id.comment[0].vars = dict(parent="vehicle")

    # Only select from vehicles
    field.widget = None # We want a simple dropdown
    ctable = s3db.supply_item_category
    itable = s3db.supply_item
    query = (ctable.is_vehicle == True) & \
            (itable.item_category_id == ctable.id)
    field.requires = IS_ONE_OF(db(query),
                               "supply_item.id",
                               "%(name)s",
                               sort=True)
    # Label changes
    table.sn.label = T("License Plate")
    s3db.asset_log.room_id.label = T("Parking Area")

    # CRUD strings
    s3.crud_strings[tablename] = Storage(
        label_create = T("Add Vehicle"),
        title_display = T("Vehicle Details"),
        title_list = T("Vehicles"),
        title_update = T("Edit Vehicle"),
        title_map = T("Map of Vehicles"),
        label_list_button = T("List Vehicles"),
        label_delete_button = T("Delete Vehicle"),
        msg_record_created = T("Vehicle added"),
        msg_record_modified = T("Vehicle updated"),
        msg_record_deleted = T("Vehicle deleted"),
        msg_list_empty = T("No Vehicles currently registered"))

    # @ToDo: Tweak the search comment

    # Defined in Model
    return s3db.asset_controller()

# =============================================================================
def vehicle_type():
    """ RESTful CRUD controller """

    return crud_controller()

# =============================================================================
def item():
    """ RESTful CRUD controller """

    # Filter to just Vehicles
    table = s3db.supply_item
    ctable = s3db.supply_item_category
    s3.filter = (table.item_category_id == ctable.id) & \
                (ctable.is_vehicle == True)

    # Limit the Categories to just those with vehicles in
    # - make category mandatory so that filter works
    field = s3db.supply_item.item_category_id
    field.requires = IS_ONE_OF(db,
                               "supply_item_category.id",
                               s3db.supply_item_category_represent,
                               sort=True,
                               filterby = "is_vehicle",
                               filter_opts = [True]
                               )

    field.label = T("Vehicle Categories")
    field.comment = PopupLink(f="item_category",
                              label=T("Add Vehicle Category"),
                              info=T("Add a new vehicle category"),
                              title=T("Vehicle Category"),
                              tooltip=T("Only Categories of type 'Vehicle' will be seen in the dropdown."))

    # CRUD strings
    s3.crud_strings["supply_item"] = Storage(
        label_create = T("Add New Vehicle Type"),
        title_display = T("Vehicle Type Details"),
        title_list = T("Vehicle Types"),
        title_update = T("Edit Vehicle Type"),
        label_list_button = T("List Vehicle Types"),
        label_delete_button = T("Delete Vehicle Type"),
        msg_record_created = T("Vehicle Type added"),
        msg_record_modified = T("Vehicle Type updated"),
        msg_record_deleted = T("Vehicle Type deleted"),
        msg_list_empty = T("No Vehicle Types currently registered"),
        msg_match = T("Matching Vehicle Types"),
        msg_no_match = T("No Matching Vehicle Types")
        )

    # Defined in the Model for use from Multiple Controllers for unified menus
    return s3db.supply_item_controller()

# =============================================================================
def item_category():
    """ RESTful CRUD controller """

    table = s3db.supply_item_category

    # Filter to just Vehicles
    s3.filter = (table.is_vehicle == True)

    # Default to Vehicles
    field = table.can_be_asset
    field.readable = field.writable = False
    field.default = True
    field = table.is_vehicle
    field.readable = field.writable = False
    field.default = True

    return crud_controller("supply", "item_category")

# END =========================================================================
