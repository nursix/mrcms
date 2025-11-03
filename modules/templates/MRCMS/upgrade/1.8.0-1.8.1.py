# Database upgrade script
#
# MRCMS Template Version 1.8.0 => 1.8.1
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.8.0-1.8.1.py
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
vtable = s3db.med_vitals

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Migrate vital parameters
#
if not failed:
    info("Migrate vital parameters...")

    query = ((vtable.rr == None) & (vtable.rf != None)) | \
            ((vtable.hr == None) & (vtable.hf != None))
    updated = db(query).update(rr = vtable.rf,
                               hr = vtable.hf,
                               modified_on = vtable.modified_on,
                               modified_by = vtable.modified_by,
                               )
    infoln("...done (%s records updated)" % updated)

# -----------------------------------------------------------------------------
# Drop unused CASE_ASSISTANT role
#
if not failed:
    info("Delete CaseAssistant role")

    rtable = auth.settings.table_group
    mtable = auth.settings.table_membership
    join = rtable.on((rtable.id == mtable.id) & \
                     (rtable.uuid == "CASE_ASSISTANT") & \
                     (rtable.deleted == False))
    row = db(mtable.deleted == False).select(mtable.id, join=join, limitby=(0, 1)).first()
    if not row:
        auth.s3_delete_role("CASE_ASSISTANT")
        infoln("...done")
    else:
        infoln("...skipped (role in use)")

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
