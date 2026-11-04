# Database upgrade script
#
# MRCMS Template Version 1.8.7 => 1.8.8
#
# Run after code upgrade like:
# edenctl run applications/eden/modules/templates/MRCMS/upgrade/1.8.7-1.8.8.py
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
#vtable = s3db.dvr_vulnerability_type

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Get all subtemplates
#
names = current.deployment_settings.get_template()
if not isinstance(names, (list, tuple)):
    names = [names]

# -----------------------------------------------------------------------------
# Deploy organisation group types
#
if not failed and "MRCMS.JUH" in names:
    info("Deploy organisation group types")

    resource = s3db.resource("org_group_type")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "group_type.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "JUH", "org_group_type.csv")

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
# Update organisation groups
#
if not failed and "MRCMS.JUH" in names:
    info("Update organisation groups")

    resource = s3db.resource("org_group")

    # File and stylesheet paths
    stylesheet = os.path.join(IMPORT_XSLT_FOLDER, "org", "group.xsl")
    filename = os.path.join(TEMPLATE_FOLDER, "JUH", "org_group.csv")

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
# Deploy shelter commission demographics
#
if not failed:
    info("Deploy shelter commission demographics...")

    names = current.deployment_settings.get_template()
    if not isinstance(names, (list, tuple)):
        names = [names]

    if "MRCMS.JUH" in names:
        resource = s3db.resource("cr_shelter_commission_demographic")

        # File and stylesheet paths
        stylesheet = os.path.join(TEMPLATE_FOLDER, "formats", "cr", "shelter_commission_demographic.xsl")
        filename = os.path.join(TEMPLATE_FOLDER, "JUH", "cr_shelter_commission_demographic.csv")

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
    else:
        infoln("...not relevant [SKIP]")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    #query = (rtable.tablename.belongs({"pr_filter"}))
    #deleted = db(query).delete()
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
