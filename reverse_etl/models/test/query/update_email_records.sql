UPDATE {TARGET_TABLE_NAME} as lead, {TARGET_TABLE_NAME_AUX} as aux SET
            lead.email = null
        WHERE lead.email = aux.email AND lead.uuid != aux.uuid