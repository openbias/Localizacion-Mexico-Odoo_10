UPDATE account_invoice AS ai SET internal_number = ai.number WHERE ai.internal_number is Null and ai.number is not Null;
UPDATE account_invoice SET uuid = substring(uuid from 1 for 8)||'-'||substring(uuid from 9 for 4)||'-'||substring(uuid from 13 for 4)||'-'||substring(uuid from 17 for 4)||'-'||substring(uuid from 21 for 12) WHERE char_length(uuid) = 32;
UPDATE res_partner AS rp SET formapago_id=metodo_pago WHERE formapago_id is Null;
UPDATE res_currency_rate AS ai SET company_id = Null;