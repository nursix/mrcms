# Database upgrade script
#
# MRCMS Template Version 1.4.0 => 1.4.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.4.0-1.4.1.py
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
ttable = s3db.dvr_case_event_type

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Upgrade case event types
#
if not failed:
    info("Upgrade case event types...")

    updated = 0

    query = (ttable.activity_id != None) & \
            (ttable.event_class != "B")
    updated += db(query).update(event_class = "B",
                                modified_by = ttable.modified_by,
                                modified_on = ttable.modified_on,
                                )

    query = (ttable.event_class == "A")
    updated += db(query).update(event_class = "C",
                                modified_by = ttable.modified_by,
                                modified_on = ttable.modified_on,
                                )

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
