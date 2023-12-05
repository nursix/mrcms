# Database upgrade script
#
# MRCMS Template Version 1.2.3 => 1.3.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.2.3-1.3.0.py
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
atable = s3db.dvr_case_appointment

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Migrate existing appointments
#
if not failed:
    info("Migrate appointments")

    # All appointments with a date but without a start date
    query = (atable.date != None) & \
            (atable.start_date == None) & \
            (atable.deleted == False)

    rows = db(query).select(atable.id,
                            atable.date,
                            atable.start_date,
                            atable.end_date,
                            )
    updated = 0
    combine = datetime.datetime.combine
    for row in rows:
        date = row.date
        start = combine(date, datetime.time(10, 0, 0))
        end = combine(date, datetime.time(10, 59, 59))
        row.update_record(start_date = start,
                          end_date = end,
                          modified_by = atable.modified_by,
                          modified_on = atable.modified_on,
                          )
        updated += 1
        info(".")

    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    #deleted = 0
    #query = (rtable.tablename == "dvr_response_type_case_activity")
    #deleted +=db(query).delete()
    #info("...%s invalid rules removed" % deleted)

    # Re-import correct rules
    bi = s3base.BulkImporter()
    filename = os.path.join(TEMPLATE_FOLDER, "auth_roles.csv")

    try:
        error = bi.import_roles(filename)
    except Exception as e:
        error = sys.exc_info()[1] or "unknown error"
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
