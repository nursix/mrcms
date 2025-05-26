# Database upgrade script
#
# MRCMS Template Version 1.7.4 => 1.7.5
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.7.4-1.7.5.py
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
ptable = s3db.pr_person

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Upgrade person records
#
if not failed:
    info("Upgrade person records...")

    query = ptable.id > 0
    updated = db(query).update(deceased=False, date_of_death=None)

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
