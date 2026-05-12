# Database upgrade script
#
# MRCMS Template Version 1.8.4 => 1.8.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.8.4-1.8.5.py
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
ctable = s3db.dvr_case
atable = s3db.dvr_response_action
ttable = s3db.dvr_response_type
stable = s3db.dvr_response_status

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Upgrade response types
#
if not failed:
    info("Upgrade response types")

    resource = s3db.resource("dvr_response_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "dvr", "response_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "dvr_response_type.csv")

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
# Fix initial consultations
#
if not failed:
    info("Fix initial consultations...")

    initial_codes = ("INI", "INI+I")
    followup_codes = ("FUP", "FUP+I")
    convert = {"FUP": "INI", "FUP+I": "INI+I"}

    # Get all consultation types {"code": id} {id: "code"}
    query = (ttable.is_consultation == True) & \
            (ttable.deleted == False)
    types = db(query).select(ttable.id, ttable.code)
    type_codes = {t.code: t.id for t in types}
    type_ids = {t.id: t.code for t in types}

    # Valid cases
    query = (ctable.archived == False) & \
            (ctable.deleted == False)
    cases = db(query)._select(ctable.person_id)

    # Closed (but not canceled) statuses
    statuses = (stable.is_closed == True) & \
               (stable.is_canceled == False) & \
               (stable.deleted == False)
    rows = db(query).select(stable.id)
    statuses = {row.id for row in rows}

    # Initial consultation types
    query = (ttable.code.belongs(initial_codes)) & \
            (ttable.is_consultation == True) & \
            (ttable.deleted == False)
    initial_types = db(query)._select(ttable.id)

    # Follow-up consultation types
    query = (ttable.code.belongs(followup_codes)) & \
            (ttable.is_consultation == True) & \
            (ttable.deleted == False)
    followup_types = db(query)._select(ttable.id)

    # All clients with follow-up conversations
    query = (atable.response_type_id.belongs(followup_types)) & \
            (atable.status_id.belongs(statuses)) & \
            (atable.person_id.belongs(cases)) & \
            (atable.deleted == False)
    rows = db(query).select(atable.person_id, distinct=True)
    updated = 0
    for row in rows:

        person_id = row.person_id

        # Check if this person has an initial consultation registered
        query = (atable.person_id == row.person_id) & \
                (atable.response_type_id.belongs(initial_types)) & \
                (atable.status_id.belongs(statuses)) & \
                (atable.deleted == False)
        if not db(query).select(atable.id, limitby=(0, 1)).first():
            # No initial consultation registered

            # Get the first follow-up consultation
            query = (atable.person_id == row.person_id) & \
                    (atable.response_type_id.belongs(followup_types)) & \
                    (atable.status_id.belongs(statuses)) & \
                    (atable.deleted == False)
            action = db(query).select(atable.id,
                                      atable.response_type_id,
                                      limitby = (0, 1),
                                      orderby = atable.start_date,
                                      ).first()

            # Get the corresponding initial type
            old_code = type_ids.get(action.response_type_id)
            new_code = convert.get(old_code)
            new_id = type_codes.get(new_code)
            if new_id:
                # Change response type
                action.update_record(response_type_id = new_id,
                                     modified_by = atable.modified_by,
                                     modified_on = atable.modified_on,
                                     )
                updated += 1
                info("+")
            else:
                info("-")
        else:
            # Initial consultation already registered
            info(".")

    infoln("...done (%s records updated)" % updated)

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
