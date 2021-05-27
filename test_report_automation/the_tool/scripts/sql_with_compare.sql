WITH ct1 AS(   SELECT
    SCENARIO_NAME,
    ROW_ID,
    OP_TRANSACTION_NAME,
    NL_TRANSACTION_NAME,
    EXPECTED_RESPONSE_TIME,
    RESULT_90_PERC,
    EXPECTED_WPM,
    RESULT_COUNT,
    RESULT_ERROR_PERC
    FROM PT_RESULTS WHERE
    RELEASE_NAME = :RELEASE_NAME AND
    APP_NAME = :APP_NAME AND
    TEST_RUN_NO = :TEST_RUN_NO AND
    TEST_TYPE = :TEST_TYPE
),
ct2 AS (
SELECT
    NL_TRANSACTION_NAME,
    RESULT_90_PERC
    FROM PT_RESULTS WHERE
    RELEASE_NAME = :old_RELEASE_NAME AND
    APP_NAME = :APP_NAME AND
    TEST_RUN_NO = :old_TEST_RUN_NO AND
    TEST_TYPE=:old_TEST_TYPE
),
ct3 AS (
SELECT
    SCENARIO_NAME,
    MIN(RESULT_COUNT) as ACHIEVED_WPM,
    COUNT(SCENARIO_NAME) AS OCCURRENCE FROM
    (
        SELECT SCENARIO_NAME,
        CASE
            WHEN LOWER(nl_transaction_name) LIKE '%login%' or
                 LOWER(nl_transaction_name) LIKE '%logout%'
            THEN 10000000
            else cast(Decode(RESULT_COUNT, '-', 10000000, RESULT_COUNT) as INT)
        END as RESULT_COUNT
        FROM PT_RESULTS
        WHERE
        RELEASE_NAME = :RELEASE_NAME AND
        APP_NAME = :APP_NAME AND
        TEST_RUN_NO = :TEST_RUN_NO AND
        TEST_TYPE = :TEST_TYPE
        ORDER BY ROW_ID
    ) GROUP BY SCENARIO_NAME
)
SELECT
ct1.SCENARIO_NAME,
ct1.OP_TRANSACTION_NAME,
ct1.EXPECTED_RESPONSE_TIME,
ct1.RESULT_90_PERC,
ct1.EXPECTED_WPM,
ct3.ACHIEVED_WPM,
--ct1.result_count,
ct1.RESULT_ERROR_PERC,
ct3.OCCURRENCE,
ct2.RESULT_90_PERC AS old_RESULT_90_PERC
FROM
ct1 LEFT OUTER JOIN ct2 ON ct1.NL_TRANSACTION_NAME = ct2.NL_TRANSACTION_NAME
LEFT OUTER JOIN ct3 ON ct1.SCENARIO_NAME = ct3.SCENARIO_NAME
ORDER BY ct1.ROW_ID