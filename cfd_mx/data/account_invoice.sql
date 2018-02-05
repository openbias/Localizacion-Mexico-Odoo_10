UPDATE account_invoice AS ai SET internal_number = ai.number;
UPDATE account_invoice SET uuid = substring(uuid from 1 for 8)||'-'||substring(uuid from 9 for 4)||'-'||substring(uuid from 13 for 4)||'-'||substring(uuid from 17 for 4)||'-'||substring(uuid from 21 for 12) WHERE char_length(uuid) = 32;
UPDATE res_partner AS rp SET formapago_id=metodo_pago;