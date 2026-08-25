SELECT
      ad_campaign,
      cohort_size,
      round(250000 / cohort_size::decimal,2) as cac,
      round(sum(order_value)::decimal / COUNT(DISTINCT user_id),2) as arppu,
      round(sum(order_value)::decimal / COUNT(order_id),2) as avg_check,
      round((sum(order_value) - 250000)::decimal / 250000 *100,2) as roi
FROM (
    SELECT
        ad_campaign,
        cohort_size,
        user_id,
        order_id,
        order_date,
        order_value
    FROM 
        table_ad_campaign_users_enriched
    LEFT JOIN table_ad_campaign_cohort_size USING (ad_campaign)
) alias3
GROUP BY
    ad_campaign, cohort_size
