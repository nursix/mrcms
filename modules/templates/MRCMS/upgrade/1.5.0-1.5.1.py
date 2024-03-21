# Database upgrade script
#
# MRCMS Template Version 1.5.0 => 1.5.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.5.0-1.5.1.py
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
stable = s3db.cr_shelter
etable = s3db.doc_entity
dtable = s3db.doc_document
rtable = s3db.s3_permission
rstable = s3db.dvr_response_status

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Fix response statuses
#
if not failed:
    info("Fix response statuses")

    query = (rstable.is_closed == None)
    db(query).update(is_closed=False)

    query = (rstable.is_canceled == None)
    db(query).update(is_canceled=False)

    query = (rstable.is_indirect_closure == None)
    db(query).update(is_indirect_closure=False)

    infoln("...done.")

# -----------------------------------------------------------------------------
# Fix realm assignment of all shelters
#
if not failed:
    info("Fix realm assignment of shelters")

    auth.set_realm_entity(stable, stable.deleted==False, force_update=True)
    infoln("...done.")

# -----------------------------------------------------------------------------
# Fix realm assignment of documents
#
if not failed:
    info("Fix realm assignments of documents")

    # Set realm for unassigned documents
    auth.set_realm_entity(dtable, dtable.realm_entity == None, force_update=True)

    # Remove realm for newsletter attachments
    doc_ids = db(etable.instance_type == "cms_newsletter")._select(etable.doc_id)
    auth.set_realm_entity(dtable, dtable.doc_id.belongs(doc_ids), force_update=True)

    infoln("...done.")

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    deleted = 0
    query = (rtable.tablename.belongs("doc_document", "doc_image"))
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
