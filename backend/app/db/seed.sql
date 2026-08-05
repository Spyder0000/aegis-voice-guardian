-- Deterministic demo rows proving the schema and dashboard contract.

INSERT INTO trust_profile (
    user_id,
    known_recipients,
    recipient_transfer_counts,
    avg_transfer_amount,
    largest_transfer_amount,
    transfer_count
) VALUES (
    'usr_demo',
    '["Landlord Account", "Mama Okafor"]'::jsonb,
    '{"landlord account": 8, "mama okafor": 5}'::jsonb,
    28500.00,
    65000.00,
    13
)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO trust_ledger (
    id,
    transaction_id,
    user_id,
    transcript,
    amount,
    recipient,
    risk_level,
    reasons,
    action,
    created_at
) VALUES
    (
        'led_seed_low',
        'tx_seed_low',
        'usr_demo',
        'Pay my usual rent transfer of 45000 to my landlord',
        45000.00,
        'Landlord Account',
        'LOW',
        '["Recipient known in transfer history", "Amount within normal pattern"]'::jsonb,
        'released',
        now() - interval '2 hours'
    ),
    (
        'led_seed_high',
        'tx_seed_high',
        'usr_demo',
        'Send 150000 to the customs officer now or my package will be seized',
        150000.00,
        'Unknown Recipient',
        'HIGH',
        '["New recipient", "Amount exceeds normal pattern", "Authority and urgency pressure detected"]'::jsonb,
        'escalated',
        now() - interval '1 hour'
    )
ON CONFLICT (id) DO NOTHING;
