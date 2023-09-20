UPDATE {TARGET_TABLE_NAME} as lead
            , {TARGET_TABLE_NAME_AUX} as aux SET
            lead.status = NULL,
            lead.deleted_at = NULL,
            lead.fingerprint = aux.fingerprint,
            lead.process_status = 'pending'
        WHERE (lead.account_uuid IS NULL AND lead.uuid = aux.uuid AND lead.deleted_at IS NOT NULL)
