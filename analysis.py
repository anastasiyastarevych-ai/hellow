import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("csv_file", nargs="?", default="supplies.csv")
args = parser.parse_args()

df = pd.read_csv(args.csv_file)

mean_price = np.mean(df["price_per_unit"])
median_quantity = np.median(df["quantity"])
std_price = np.std(df["price_per_unit"])

print("Середня ціна:", round(mean_price, 2))
print("Медіана кількості:", median_quantity)
print("Стандартне відхилення ціни:", round(std_price, 2))

profit = (df["quantity"] * df["price_per_unit"]).groupby(df["supplier"]).sum()
best_supplier = profit.idxmax()
print("Постачальник з найбільшим прибутком:", best_supplier, round(profit.max(), 2))

category_quantity = df.groupby("category")["quantity"].sum()
print("Кількість за категоріями:")
print(category_quantity)

low_supply = df[df["quantity"] < 100]
low_supply.to_csv("low_supply.csv", index=False)

df["total_price"] = df["quantity"] * df["price_per_unit"]

sorted_df = df.sort_values("total_price", ascending=False)
print("Топ-3 за total_price:")
print(sorted_df.head(3))

with open("report.txt", "w", encoding="utf-8") as f:
    f.write("Звіт по поставках\n\n")
    f.write(f"Середня ціна: {mean_price:.2f}\n")
    f.write(f"Медіана кількості: {median_quantity}\n")
    f.write(f"Стандартне відхилення ціни: {std_price:.2f}\n")
    f.write(f"Постачальник з найбільшим прибутком: {best_supplier} ({profit.max():.2f})\n")
    f.write("Файл з дефіцитними поставками: low_supply.csv\n")

plt.bar(category_quantity.index, category_quantity.values)
plt.title("Розподіл кількості препаратів за категоріями")
plt.xlabel("Категорія")
plt.ylabel("Кількість")
plt.savefig("chart.png")
plt.show()