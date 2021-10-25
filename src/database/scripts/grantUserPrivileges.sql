GRANT CONNECT, RESOURCE, DBA TO online_claims;
GRANT UNLIMITED TABLESPACE TO online_claims;
GRANT REFERENCES ON client.users to online_claims;
GRANT REFERENCES ON client.bank_branches to online_claims;
GRANT UNLIMITED TABLESPACE TO online_claims;