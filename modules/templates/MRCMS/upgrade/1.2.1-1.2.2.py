# Database upgrade script
#
# MRCMS Template Version 1.2.1 => 1.2.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.2.1-1.2.2.py
#
import sys

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
ftable = s3db.pr_filter

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Introduce residents-only flag for event types
#
if not failed:
    info("Upgrade case event types")

    query = (ttable.id > 0)
    db(query).update(residents_only=False)

    # Food distribution events are residents-only by default
    query = (ttable.event_class == "F")
    db(query).update(residents_only=True)

    infoln("...done")

# -----------------------------------------------------------------------------
# Fix realm entities for pr_filter
#
if not failed:
    info("Fix saved filters ownership")

    auth.set_realm_entity(ftable, ftable.deleted==False, force_update=True)

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
