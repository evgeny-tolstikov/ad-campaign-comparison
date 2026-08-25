import datetime
import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image # insert image into report.xlsx

# xlsx export from Redash has "queryname_YYYY_MM_DD.xlsx" file name
current_date = datetime.date.today().strftime('%Y_%m_%d')
df_orders = pd.read_excel(f"table_ad_campaigns_users_and_their_orders_{current_date}.xlsx")

campaign_stats = df_orders.groupby("ad_campaign", as_index=False).agg(
    total_revenue = ("order_value", "sum"),
    paying_users = ("user_id", "nunique"),
    orders_count = ("order_id", "nunique")
)

# summary metrics table: cac, arppu, aov, roi
df_summary = pd.read_excel("table_ad_campaigns_processed.xlsx")
df_summary = df_summary.merge(campaign_stats, on = "ad_campaign", how = "left")

df_summary["cac"] = round(df_summary["budget"] / df_summary["cohort_size"],2)
df_summary["arppu"] = round(df_summary["total_revenue"] / df_summary["paying_users"],2)
df_summary["aov"] = round(df_summary["total_revenue"] / df_summary["orders_count"],2)
df_summary["roi"] = round((df_summary["total_revenue"] - df_summary["budget"]) / df_summary["budget"] * 100,2)

# daily metrics table: retention, roi_cumulative
df_daily = df_orders.groupby(["ad_campaign", "order_date"], as_index=False).agg(
    revenue_this_day = ("order_value", "sum"),
    paying_users_this_day = ("user_id", "nunique"),
    orders_count_this_day = ("order_id", "nunique")
)

df_daily = df_daily.sort_values(["ad_campaign", "order_date"])
df_daily["ad_campaign_day"] = df_daily.groupby("ad_campaign").cumcount()

df_daily = df_daily.merge(
    df_summary[["ad_campaign", "cohort_size", "budget"]],
    on = "ad_campaign",
    how = "left"
)

df_daily["retention"] = round(df_daily["paying_users_this_day"] / df_daily["cohort_size"] * 100,2)
df_daily["revenue_cumulative"] = df_daily.groupby("ad_campaign")["revenue_this_day"].cumsum()
df_daily["roi_cumulative"] = round( (df_daily["revenue_cumulative"] - df_daily["budget"]) / df_daily["budget"] * 100 ,2)

# result table
df_result = df_summary[["ad_campaign", "budget", "date_start", "cohort_size", "cac", "arppu", "aov", "roi"]]
# result table: ad campaign payback day (if exists)
payback_day = (
    df_daily[df_daily["roi_cumulative"] >= 0]
    .groupby("ad_campaign")["ad_campaign_day"]
    .min()
    .reset_index()
    .rename(columns={"ad_campaign_day": "payback_day"})
)
df_result = df_result.merge(payback_day, on="ad_campaign", how="left")

# result table: retention D1, D7, D30 (if exists)
target_days = [1, 7, 30]
retention_subtable = df_daily[df_daily["ad_campaign_day"].isin(target_days)].pivot(
    index="ad_campaign",
    columns="ad_campaign_day",
    values="retention"
)
retention_subtable.columns = [f"retention_d{col}" for col in retention_subtable.columns]
retention_subtable = retention_subtable.reset_index()
df_result = df_result.merge(retention_subtable, on="ad_campaign", how="left")

#result table: user friendly column names
df_result = df_result.rename(columns={
    "budget": "Бюджет, ₽",
    "date_start": "Дата начала",
    "cohort_size": "Привлечено пользователей",
    "cac": "CAC, ₽",
    "arppu": "ARPPU, ₽",
    "aov": "AOV, ₽",
    "roi": "ROI, %",
    "payback_day": "День окупаемости РК (если есть)",
    "retention_d1": "Retention D1, %",
    "retention_d7": "Retention D7, %",
    "retention_d30": "Retention D30, %"
    })
df_result = df_result.set_index("ad_campaign").T

# result table: save as xlsx
df_result.to_excel("ad_campaigns_report.xlsx", sheet_name="summary", index=True)

# retention: pivot --> plot --> save plot as png
retention_graph = df_daily.pivot(index="ad_campaign_day", columns="ad_campaign", values="retention").plot(
    marker="o", title="Retention по дням", figsize=(8, 5)
)
retention_png = retention_graph.get_figure()
retention_png.savefig("chart_retention.png", bbox_inches="tight")
plt.close(retention_png)

# roi_cumulative: pivot --> plot --> save plot as png
roi_graph = df_daily.pivot(index="ad_campaign_day", columns="ad_campaign", values="roi_cumulative").plot(
    marker="o", title="ROI cumulative по дням", figsize=(8, 5)
)
roi_graph.axhline(y=0, color="grey", linestyle="--")
roi_png = roi_graph.get_figure()
roi_png.savefig("chart_roi_cumulative.png", bbox_inches="tight")
plt.close(roi_png)

# open report.xlsx and insert 2 plot images
wb = load_workbook("ad_campaigns_report.xlsx")
ws = wb["summary"]

img1 = Image("chart_retention.png")
img1.anchor = "A14"
ws.add_image(img1)

img2 = Image("chart_roi_cumulative.png")
img2.anchor = "L14"
ws.add_image(img2)

wb.save("ad_campaigns_report.xlsx")