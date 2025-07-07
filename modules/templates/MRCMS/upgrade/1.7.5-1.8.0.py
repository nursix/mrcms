# Database upgrade script
#
# MRCMS Template Version 1.7.5 => 1.8.0
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.7.5-1.8.0.py
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
rtable = s3db.s3_permission
pftable = s3db.pr_filter
uftable = s3db.usr_filter
dtable = s3db.cms_newsletter_distribution

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

settings.base.debug = True

# -----------------------------------------------------------------------------
# Migrate saved filters
#
if not failed:
    info("Migrate saved filters...")

    left = uftable.on(uftable.uuid == pftable.uuid)
    query = (pftable.id > 0) & \
            (uftable.id == None)
    rows = db(query).select(pftable.ALL, left=left, orderby=pftable.id)

    # Get all newsletter distributions linked to these rows
    query = dtable.filter_id.belongs({row.id for row in rows})
    distributions = db(query).select(dtable.id, dtable.filter_id)
    dist_dict = {}
    for d in distributions:
        if d.filter_id in dist_dict:
            dist_dict[d.filter_id].append(d)
        else:
            dist_dict[d.filter_id] = [d]

    migrated = 0
    for row in rows:
        record = {fn:row[fn] for fn in uftable.fields if fn in row and fn != "id"}
        saved_filter_id = uftable.insert(**record)

        migrated += 1

        # Update all related newsletter distributions
        distributions = dist_dict.get(row.id)
        if not distributions:
            info(".")
            continue
        for d in distributions:
            d.update_record(saved_filter_id=saved_filter_id,
                            modified_on = dtable.modified_on,
                            modified_by = dtable.modified_by,
                            )
        info("+")

    infoln("...done (%s filters migrated)" % migrated)

# -----------------------------------------------------------------------------
# Upgrade user roles
#
if not failed:
    info("Upgrade user roles")

    # Delete invalid rules
    deleted = 0
    query = (rtable.tablename.belongs({"pr_filter"}))
    deleted += db(query).delete()
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
