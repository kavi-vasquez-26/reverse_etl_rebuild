UPDATE {TARGET_TABLE_NAME} as lead, {TARGET_TABLE_NAME_AUX} as aux SET
            lead.fingerprint = IF(lead.client_id!=aux.client_id,null,lead.fingerprint)
        WHERE aux.uuid = lead.uuid AND (lead.account_uuid IS NULL OR lead.fingerprint IS NULL)