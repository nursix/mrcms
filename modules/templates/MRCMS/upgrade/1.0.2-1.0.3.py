# Database upgrade script
#
# MRCMS Template Version 1.0.2 => 1.0.3
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.0.2-1.0.3.py
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
ptable = s3db.pr_person
rtable = s3db.s3_permission

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Update realms
#
if not failed:
    info("Update realms")

    # Configure realm components
    s3db.configure("pr_person",
                   realm_components = ("case_activity",
                                       "case_details",
                                       "case_language",
                                       "case_note",
                                       "residence_status",
                                       "response_action",
                                       "group_membership",
                                       "identity",
                                       "person_details",
                                       "person_tag",
                                       "shelter_registration",
                                       "shelter_registration_history",
                                       "address",
                                       "contact",
                                       "contact_emergency",
                                       "image",
                                       ),
                   )

    auth.set_realm_entity(ptable, ptable.id>0, force_update=True)
    infoln("...done")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    deleted = 0
    query = (rtable.controller == "pr") & \
            (rtable.function == "contact")
    deleted += db(query).delete()

    query = (rtable.controller == "cr")
    deleted += db(query).delete()

    query = (rtable.tablename.like("cr_%"))
    deleted +=db(query).delete()

    info("...%s invalid rules removed" % deleted)

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
