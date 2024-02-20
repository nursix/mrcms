# Database upgrade script
#
# MRCMS Template Version 1.4.1 => 1.4.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.4.1-1.4.2.py
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
itable = s3db.security_seized_item
dtable = s3db.security_seized_item_depository
ctable = s3db.dvr_case
utable = s3db.auth_user

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Fix ownership of seized item depositories
#
if not failed:
    info("Fix ownership of seized item depositories...")

    updated = removed = 0

    query = (dtable.organisation_id == None)
    depositories = db(query).select(dtable.id,
                                    dtable.created_by,
                                    )

    join = ctable.on(ctable.person_id == itable.person_id)
    for depository in depositories:
        # Lookup the case organisation of the owner of the first deposited item
        query = (itable.depository_id == depository.id)
        row = db(query).select(ctable.organisation_id,
                               join = join,
                               limitby = (0, 1),
                               orderby = ~itable.created_on,
                               ).first()
        organisation_id = row.organisation_id if row else None

        if not organisation_id:
            # Try the organisation_id of the user who created the depository
            row = db(utable.id == depository.created_by).select(utable.organisation_id,
                                                                limitby = (0, 1),
                                                                ).first()
            if row:
                organisation_id = row.organisation_id

        if organisation_id:
            # Assign depository to this organisation
            depository.update_record(organisation_id = organisation_id)
            info("+")
            updated += 1

            # Remove all items from this depository which do not belong to this organisation
            query = (itable.depository_id == depository.id) & \
                    (ctable.organisation_id != row.organisation_id)
            items = db(query)._select(itable.id, join=join)
            db(itable.id.belongs(items)).update(depository_id=None)
        else:
            # Remove the depository if it cannot be assigned
            depository.delete_record()
            info("-")
            removed += 1

    # Set realm entity for depositories
    auth.set_realm_entity(dtable, dtable.id>0, force_update=True)

    infoln("...done (%s depositories updated, %s removed)" % (updated, removed))

# -----------------------------------------------------------------------------
# Fix ownership of seized items
#
if not failed:
    info("Fix ownership of seized items")

    auth.set_realm_entity(itable, itable.id>0, force_update=True)

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
