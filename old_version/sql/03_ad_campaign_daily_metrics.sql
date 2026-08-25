SELECT
    order_date,
    paid_user_count,
    round(paid_user_count::decimal / cohort_size * 100,2) as retention,
    round((sum(revenue_this_day) OVER (partition by ad_campaign ORDER by order_date)::decimal - 250000) / 250000 * 100,2) as roi_cumulative,
    ad_campaign,
    row_number() OVER (PARTITION BY ad_campaign ORDER BY order_date) - 1 as ad_campaign_day
FROM (
    SELECT
        order_date,
        sum(order_value) as revenue_this_day,
        COUNT(distinct user_id) as paid_user_count,
        ad_campaign,
        cohort_size
    FROM
        table_ad_campaign_users_enriched
    LEFT JOIN table_ad_campaign_cohort_size USING (ad_campaign)
    GROUP BY
        ad_campaign, order_date, cohort_size
    ) stats_by_date_with_cohort_size
