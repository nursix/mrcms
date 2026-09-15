# Database upgrade script
#
# MRCMS Template Version 1.8.6 => 1.8.7
#
# Run after code upgrade like:
# edenctl run applications/eden/modules/templates/MRCMS/upgrade/1.8.6-1.8.7.py
#
import sys
import datetime

from core import S3Duplicate

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
vtable = s3db.dvr_vulnerability_type

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Update vulnerability types
#
if not failed:
    info("Update vulnerability types...")

    query = (vtable.code == "SOGI") & (vtable.deleted == False)
    row = db(query).select(vtable.id, limitby=(0, 1)).first()

    if not row:
        change = ("LGBQTi", "LGBTQi")
        for code in change:
            query = (vtable.code == code) & (vtable.deleted == False)
            updated = db(query).update(code = "SOGI",
                                       modified_on = vtable.modified_on,
                                       modified_by = vtable.modified_by,
                                       )
            if updated:
                break
        if updated:
            infoln("done.")
        else:
            infoln("failed.")
            failed = True
    else:
        infoln("already done [SKIP].")

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
