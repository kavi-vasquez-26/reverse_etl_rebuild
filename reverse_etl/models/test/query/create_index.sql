ALTER TABLE {TARGET_TABLE_NAME_AUX}
  ADD INDEX idx_lead_aux_sword_uuid (sword_uuid)
, ADD INDEX idx_lead_aux_fingerprint (fingerprint)
, ADD INDEX idx_lead_aux_email (email)
, ADD INDEX idx_lead_aux_uuid (uuid);