# Database upgrade script
#
# MRCMS Template Version 1.6.3 => 1.6.4
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.6.3-1.6.4.py
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
rtable = s3db.cr_shelter_registration_history

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Fix shelter registration history
#
if not failed:
    info("Fix shelter registration history")

    # Get person_id, date and status of any duplicate entries
    query = (rtable.deleted == False)

    number = rtable.id.count()
    rows = db(query).select(rtable.person_id,
                            rtable.date,
                            rtable.status,
                            number,
                            groupby = (rtable.person_id,
                                       rtable.date,
                                       rtable.status,
                                       ),
                            having = number > 1,
                            )

    updated = 0
    for row in rows:
        entry = row.cr_shelter_registration_history
        query = (rtable.person_id == entry.person_id) & \
                (rtable.date == entry.date) & \
                (rtable.status == entry.status)
        records = db(query).select(rtable.id,
                                   rtable.created_on,
                                   rtable.date,
                                   orderby = (rtable.created_on, rtable.id),
                                   )
        record_ids = [r.id for r in records]
        query = rtable.id.belongs(record_ids[1:])
        cnt = db(query).update(date = rtable.created_on,
                               modified_by = rtable.modified_by,
                               modified_on = rtable.modified_on,
                               )
        updated += cnt
        info("." * cnt)

    infoln("...done (%s records fixed)" % updated)

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
