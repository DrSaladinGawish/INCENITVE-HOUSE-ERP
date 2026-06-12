import csv, io
from datetime import date


def trial_balance_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Account Code", "Account Name", "Account Type", "Debit", "Credit", "Balance"])
    for acc in data.get("accounts", []):
        writer.writerow([
            acc.get("account_code", ""),
            acc.get("account_name", ""),
            acc.get("account_type", ""),
            f'{acc.get("debit", 0):.2f}',
            f'{acc.get("credit", 0):.2f}',
            f'{acc.get("balance", 0):.2f}',
        ])
    writer.writerow([])
    writer.writerow(["", "", "TOTAL", f'{data.get("total_debit", 0):.2f}', f'{data.get("total_credit", 0):.2f}', ""])
    writer.writerow(["As of", data.get("as_of_date", "")])
    return output.getvalue()


def profit_loss_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Account Code", "Account Name", "Amount"])
    writer.writerow(["", "REVENUES", ""])
    for rev in data.get("revenues", []):
        writer.writerow([rev.get("account_code", ""), rev.get("account_name", ""), f'{rev.get("amount", 0):.2f}'])
    writer.writerow(["", "Total Revenue", f'{data.get("total_revenue", 0):.2f}'])
    writer.writerow([])
    writer.writerow(["", "EXPENSES", ""])
    for exp in data.get("expenses", []):
        writer.writerow([exp.get("account_code", ""), exp.get("account_name", ""), f'{exp.get("amount", 0):.2f}'])
    writer.writerow(["", "Total Expenses", f'{data.get("total_expense", 0):.2f}'])
    writer.writerow([])
    writer.writerow(["", "NET INCOME", f'{data.get("net_income", 0):.2f}'])
    writer.writerow(["Period", f'{data.get("from_date", "")} to {data.get("to_date", "")}'])
    return output.getvalue()


def balance_sheet_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Account Code", "Account Name", "Balance"])
    writer.writerow(["", "ASSETS", ""])
    for a in data.get("assets", []):
        writer.writerow([a.get("account_code", ""), a.get("account_name", ""), f'{a.get("balance", 0):.2f}'])
    writer.writerow(["", "Total Assets", f'{data.get("total_assets", 0):.2f}'])
    writer.writerow([])
    writer.writerow(["", "LIABILITIES", ""])
    for l in data.get("liabilities", []):
        writer.writerow([l.get("account_code", ""), l.get("account_name", ""), f'{l.get("balance", 0):.2f}'])
    writer.writerow(["", "Total Liabilities", f'{data.get("total_liabilities", 0):.2f}'])
    writer.writerow([])
    writer.writerow(["", "EQUITY", ""])
    for e in data.get("equity", []):
        writer.writerow([e.get("account_code", ""), e.get("account_name", ""), f'{e.get("balance", 0):.2f}'])
    writer.writerow(["", "Total Equity", f'{data.get("total_equity", 0):.2f}'])
    writer.writerow(["As of", data.get("as_of_date", "")])
    return output.getvalue()


def cash_flow_csv(data: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Narration", "Amount", "JV Number", "Contra Accounts"])
    writer.writerow(["", "OPERATING ACTIVITIES", "", "", ""])
    for op in data.get("operating", []):
        writer.writerow([op.get("date", ""), op.get("narration", ""), f'{op.get("amount", 0):.2f}', op.get("jv_number", ""), "; ".join(op.get("contra_accounts", []))])
    writer.writerow(["", "Net Operating", f'{data.get("net_operating", 0):.2f}', "", ""])
    writer.writerow([])
    writer.writerow(["", "INVESTING ACTIVITIES", "", "", ""])
    for inv in data.get("investing", []):
        writer.writerow([inv.get("date", ""), inv.get("narration", ""), f'{inv.get("amount", 0):.2f}', inv.get("jv_number", ""), "; ".join(inv.get("contra_accounts", []))])
    writer.writerow(["", "Net Investing", f'{data.get("net_investing", 0):.2f}', "", ""])
    writer.writerow([])
    writer.writerow(["", "FINANCING ACTIVITIES", "", "", ""])
    for fin in data.get("financing", []):
        writer.writerow([fin.get("date", ""), fin.get("narration", ""), f'{fin.get("amount", 0):.2f}', fin.get("jv_number", ""), "; ".join(fin.get("contra_accounts", []))])
    writer.writerow(["", "Net Financing", f'{data.get("net_financing", 0):.2f}', "", ""])
    writer.writerow([])
    writer.writerow(["", "NET CHANGE", f'{data.get("net_change", 0):.2f}', "", ""])
    writer.writerow(["", "Opening Balance", f'{data.get("opening_balance", 0):.2f}', "", ""])
    writer.writerow(["", "Closing Balance", f'{data.get("closing_balance", 0):.2f}', "", ""])
    writer.writerow(["Period", f'{data.get("from_date", "")} to {data.get("to_date", "")}', "", "", ""])
    return output.getvalue()
