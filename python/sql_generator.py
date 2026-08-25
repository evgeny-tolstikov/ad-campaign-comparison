import pandas as pd

df = pd.read_excel("table_ad_campaigns_raw.xlsx").copy()

# create table_ad_campaigns_processed.xlsx
df["cohort_size"] = df["user_id_list"].apply(lambda x: len(x.split(",")))
df.to_excel("table_ad_campaigns_processed.xlsx", header=True, index=False)

# SQL-query: CTE part
cte_part = []
for _, row in df.iterrows():
    ad_campaign_block = (
        "    SELECT\n"
        f"    '{row['ad_campaign']}' as ad_campaign,\n"
        f"    unnest(array[{row['user_id_list']}]) as user_id"
    )
    cte_part.append(ad_campaign_block)
sql_query_cte_part = "\nUNION\n".join(cte_part)

# SQL-query: main part
sql_query_main_part = """
SELECT
    user_id,
    order_id,
    order_date,
    sum(price) as order_value,
    ad_campaign
FROM (
    SELECT
        user_id,
        order_id,
        order_date,
        unnest(product_ids) as product_id,
        ad_campaign
    FROM (
        SELECT
            ad_campaign,
            user_id,
            order_id,
            time::date as order_date
        FROM
            table_ad_campaign_users
        LEFT JOIN
            user_actions USING (user_id)
        WHERE
            user_actions.action = 'create_order'
            AND order_id NOT IN (SELECT order_id FROM user_actions WHERE action = 'cancel_order')
        ) alias1
    LEFT JOIN
        orders USING (order_id)
) alias2
LEFT JOIN
    products USING(product_id)
GROUP BY
    user_id, order_id, order_date, ad_campaign
"""

# SQL-query: full version
sql_query_full = (
        "WITH \n"
        "table_ad_campaign_users as (\n"
        f"{sql_query_cte_part}\n"
        ")\n"
        f"{sql_query_main_part}"
)

# generate sql-file with full query
with open('enrich_ad_campaign_users_with_their_orders.sql', 'w', encoding='utf-8') as f:
    f.write(sql_query_full)