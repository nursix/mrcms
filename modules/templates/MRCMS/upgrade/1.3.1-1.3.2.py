# Database upgrade script
#
# MRCMS Template Version 1.3.1 => 1.3.2
#
# Execute in web2py folder after code upgrade like:
# python web2py.py -S eden -M -R applications/eden/modules/templates/MRCMS/upgrade/1.3.1-1.3.2.py
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
rtable = s3db.cr_shelter_registration
htable = s3db.cr_shelter_registration_history

# Paths
IMPORT_XSLT_FOLDER = os.path.join(request.folder, "static", "formats", "s3csv")
TEMPLATE_FOLDER = os.path.join(request.folder, "modules", "templates", "MRCMS")

# -----------------------------------------------------------------------------
# Fix shelter registration history
#
if not failed:
    info("Fix shelter registration history...")

    # Get all shelter registrations
    query = (rtable.deleted == False)
    rows = db(query).select(rtable.id,
                            rtable.person_id,
                            rtable.shelter_id,
                            rtable.registration_status,
                            rtable.check_in_date,
                            rtable.check_out_date,
                            rtable.modified_on,
                            rtable.modified_by,
                            )

    added, fixed = 0, 0
    for row in rows:
        status = row.registration_status
        shelter_id = row.shelter_id
        person_id = row.person_id
        now = datetime.datetime.utcnow()

        # Get last history entry for the same person_id
        query = (htable.person_id == person_id) & \
                (htable.deleted != True)
        entry = db(query).select(htable.id,
                                 htable.shelter_id,
                                 htable.status,
                                 htable.date,
                                 htable.modified_by,
                                 htable.modified_on,
                                 orderby = (~htable.date, ~htable.id),
                                 limitby = (0, 1)
                                 ).first()

        # Determine the effective date
        if status == 2:
            effective_date_field = "check_in_date"
        elif status == 3:
            effective_date_field = "check_out_date"
        else:
            effective_date_field = None

        if entry.status != status or entry.shelter_id != shelter_id:
            # Last history entry has a different status or is for a
            # different shelter than the current registration, i.e.
            # there is an entry missing from the history, which must
            # be added in order to have future movements recorded
            # correctly

            # We must assume that registration effective date is wrong
            # (progressed from the actual date of the movement), so we
            # cannot use that for the history entry
            # => however, the movement cannot have happened before the
            #    latest history entry (which then represents a previous
            #    movement), nor after the effective date (except when
            #    the current status is "planned", which does not have
            #    an effective date - then we assume "now")
            # => so, we use the latest possible date here, even though this
            #    is unlikely to be the correct date of the last movement
            effective_date = row[effective_date_field] if effective_date_field else None
            latest = min(effective_date, now) if effective_date else now
            date = max(entry.date, latest) if entry.date else latest

            # Add missing history entry with speculative date
            data = {"person_id": person_id,
                    "shelter_id": shelter_id,
                    "previous_status": entry.status,
                    "status": status,
                    "date": date,
                    "created_on": date,
                    "created_by": row.modified_by,
                    "modified_on": date,
                    "modified_by": row.modified_by,
                    }
            record_id = data["id"] = htable.insert(**data)

            # Postprocess create
            s3db.update_super(htable, data)
            auth.s3_set_record_owner(htable, record_id)
            s3db.onaccept(htable, data, method="create")

            info("+")
            added += 1

        elif effective_date_field and \
             shelter_id == entry.shelter_id and status == entry.status:

            update = {}

            # Current status is checked-in or checked-out, but the effective
            # status date could be wrong (progressed when saving the person
            # record) - yet the entry date would be correct in this case
            # => fix the effective date
            if row[effective_date_field] != entry.date:
                update[effective_date_field] = entry.date

            # If the current status is checked-out, and the immediately preceding
            # history entry is the check-in for the same shelter, then we can also
            # correct the check-in date in the registration in case it is wrong
            if status == 3:
                query = (htable.person_id == person_id) & \
                        (htable.date <= entry.date) & \
                        (htable.id != entry.id)
                preceding = db(query).select(htable.shelter_id,
                                             htable.status,
                                             htable.date,
                                             limitby = (0, 1),
                                             orderby = (~htable.date, ~htable.id),
                                             ).first()
                if preceding and preceding.shelter_id == entry.shelter_id and \
                   preceding.status == 2 and preceding.date != row.check_in_date:
                    update["check_in_date"] = preceding.date

            if update:
                update["modified_by"] = entry.modified_by
                update["modified_on"] = entry.modified_on
                row.update_record(**update)
                info("o")
                fixed += 1

        else:
            # Nothing we can do (some entries could still be wrong, though)
            info(".")

        if status not in (2, 3) and (row.check_in_date or row.check_out_date):
            # Remove both effective date fields when neither
            # checked-in nor checked-out
            row.update_record(**{"check_in_date": None,
                                 "check_out_date": None,
                                 "modified_by": rtable.modified_by,
                                 "modified_on": rtable.modified_on,
                                 })
            info("-")
            fixed += 1

    infoln("...done (%s entries added, %s registrations fixed)" % (added, fixed))

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
