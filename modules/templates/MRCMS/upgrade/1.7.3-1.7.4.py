# Database upgrade script
#
# MRCMS Template Version 1.7.3 => 1.7.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.7.3-1.7.4.py
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

settings.base.debug = True

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    #deleted = 0
    #query = (rtable.tablename.belongs("doc_document", "doc_image"))
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
