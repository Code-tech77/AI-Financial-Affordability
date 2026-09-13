import pandas as pd
import numpy as np
import datetime
import math
import re

# Multimodal Image OCR Extraction dictionary for the 16 dataset images
IMAGE_AMOUNTS = {
    'event_253': 4365000.0,   # image_01: Payslip Net Pay IDR
    'event_1442': 100000.0,   # image_02: Rent balance due INR
    'event_1545': 41272.0,    # image_03: Riddhi Siddhi bill INR
    'event_1700': 2854.0,     # image_04: Groceries bill INR
    'event_1786': 704.05,     # image_05: Airtel bill INR
    'event_3051': 1995.0,     # image_06: Blink invoice INR
    'event_3231': 8528.0,     # image_07: Nagarjuna tax invoice INR
    'event_4535': 15339.0,    # image_08: Property maintenance INR
    'event_5170': 723.0,      # image_09: Water bill INR
    'event_6033': 79679.26,   # image_10: Grocery invoice INR
    'event_6859': 3650.0,     # image_11: Hospital bill INR
    'event_7307': 33.50,      # image_12: Taxi fare USD
    'event_7941': 2298.0,     # image_13: Tote bag order INR
    'event_9421': 4543.0,     # image_14: Pharmacy bill INR
    'event_9806': 9968.0,     # image_15: IndiGo flight INR
    'event_10521': 393.22,    # image_16: EV charge invoice INR
}

def parse_date(d_str):
    if not isinstance(d_str, str) or not d_str or str(d_str) == 'nan':
        return None
    try:
        return datetime.datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def format_date(d):
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")

def fmt_amt(val):
    if val is None or math.isnan(val):
        return "0"
    if abs(val - round(val)) < 1e-5:
        return f"{int(round(val)):,}"
    return f"{val:,.2f}"

def fmt_amt_plain(val):
    if val is None or math.isnan(val):
        return "0"
    if abs(val - round(val)) < 1e-5:
        return f"{int(round(val))}"
    return f"{val:.2f}"

class CurrencyConverter:
    def __init__(self, exchange_rates_df):
        self.rates = {}
        for _, row in exchange_rates_df.iterrows():
            r_date = parse_date(row['rate_date'])
            from_c = str(row['from_currency']).strip()
            to_c = str(row['to_currency']).strip()
            rate = float(row['rate'])
            if r_date not in self.rates:
                self.rates[r_date] = {}
            self.rates[r_date][(from_c, to_c)] = rate
            if rate > 0:
                self.rates[r_date][(to_c, from_c)] = 1.0 / rate

    def convert(self, amount, from_curr, to_curr, date_obj):
        if from_curr == to_curr or amount == 0 or math.isnan(amount):
            return amount
        if date_obj is None:
            dates = sorted(self.rates.keys())
            date_obj = dates[0] if dates else datetime.date(2024, 1, 1)

        available_dates = sorted(self.rates.keys())
        target_date = date_obj
        if target_date not in self.rates:
            priors = [d for d in available_dates if d <= target_date]
            if priors:
                target_date = max(priors)
            else:
                target_date = min(available_dates)

        day_rates = self.rates.get(target_date, {})
        if (from_curr, to_curr) in day_rates:
            return amount * day_rates[(from_curr, to_curr)]
        
        for mid in ['EUR', 'USD', 'INR', 'ZAR', 'IDR']:
            if (from_curr, mid) in day_rates and (mid, to_curr) in day_rates:
                return amount * day_rates[(from_curr, mid)] * day_rates[(mid, to_curr)]

        return amount

class FinancialEngine:
    def __init__(self, dataset_dir='dataset'):
        self.dataset_dir = dataset_dir
        self.load_data()

    def load_data(self):
        self.profiles = pd.read_csv(f"{self.dataset_dir}/financial_profiles.csv")
        self.events = pd.read_csv(f"{self.dataset_dir}/financial_events.csv")
        self.exchange_rates = pd.read_csv(f"{self.dataset_dir}/exchange_rates.csv")
        self.requests = pd.read_csv(f"{self.dataset_dir}/requests.csv")
        self.payment_options = pd.read_csv(f"{self.dataset_dir}/request_payment_options.csv")
        self.messages = pd.read_csv(f"{self.dataset_dir}/messages.csv")
        self.images = pd.read_csv(f"{self.dataset_dir}/images.csv")
        self.converter = CurrencyConverter(self.exchange_rates)

    def process_messages(self, user_id):
        """Extract user specific updates from messages."""
        user_msgs = self.messages[self.messages['user_id'] == user_id]
        updates = {
            'salary_amount_override': None,
            'salary_date_override': None,
            'cancelled_events': set(),
            'pending_credits_to_ignore': set()
        }
        for _, m in user_msgs.iterrows():
            txt = str(m['message_text'])
            
            sal_match = re.search(r'(?:salary|gaji|pay)[^\d]*([A-Z]{3})?\s*([\d,]+(?:\.\d+)?)', txt, re.IGNORECASE)
            if sal_match and ('naik menjadi' in txt.lower() or 'confirmed' in txt.lower() or 'reduced to' in txt.lower() or 'monthly pay is' in txt.lower()):
                try:
                    val_str = sal_match.group(2).replace(',', '')
                    updates['salary_amount_override'] = float(val_str)
                except Exception:
                    pass

            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', txt)
            if date_match and ('payroll date' in txt.lower() or 'resumes on' in txt.lower() or 'scheduled for' in txt.lower()):
                updates['salary_date_override'] = parse_date(date_match.group(1))

            if 'cancel' in txt.lower() or 'failed' in txt.lower():
                rel_ev = m.get('related_event_id')
                if pd.notna(rel_ev):
                    updates['cancelled_events'].add(rel_ev)
            
            if 'pending' in txt.lower() and ('bonus' in txt.lower() or 'commission' in txt.lower() or 'payout' in txt.lower()):
                rel_ev = m.get('related_event_id')
                if pd.notna(rel_ev):
                    updates['pending_credits_to_ignore'].add(rel_ev)

        return updates

    def get_user_recurring_cashflows(self, user_id, req_date_str, home_curr, msg_updates):
        """Extract historical recurring debits and salary pattern for user."""
        req_dt = parse_date(req_date_str)
        user_events = self.events[self.events['user_id'] == user_id].copy()

        for idx, row in user_events.iterrows():
            if pd.isna(row['amount']):
                ev_id = row['event_id']
                if ev_id in IMAGE_AMOUNTS:
                    user_events.at[idx, 'amount'] = IMAGE_AMOUNTS[ev_id]

        user_events = user_events[~user_events['status'].isin(['failed', 'cancelled', 'unrealized'])]

        sal_events = user_events[(user_events['category'] == 'salary') & (user_events['direction'] == 'credit')]
        salary_day = 15
        salary_amt = 0.0

        if not sal_events.empty:
            last_sal = sal_events.iloc[-1]
            sal_dt = parse_date(last_sal['event_date'])
            if sal_dt:
                salary_day = sal_dt.day
            salary_amt = float(last_sal['amount']) if pd.notna(last_sal['amount']) else 0.0

        if msg_updates['salary_amount_override']:
            salary_amt = msg_updates['salary_amount_override']

        if msg_updates['salary_date_override']:
            salary_day = msg_updates['salary_date_override'].day

        if req_dt.day <= salary_day:
            next_salary_dt = datetime.date(req_dt.year, req_dt.month, min(salary_day, 28))
        else:
            m = req_dt.month % 12 + 1
            y = req_dt.year + (1 if req_dt.month == 12 else 0)
            next_salary_dt = datetime.date(y, m, min(salary_day, 28))

        days_to_payday = (next_salary_dt - req_dt).days

        hist_start = req_dt - datetime.timedelta(days=35)
        hist_debits = user_events[
            (user_events['direction'] == 'debit') & 
            (user_events['event_date'] >= str(hist_start)) & 
            (user_events['event_date'] <= str(req_dt))
        ]

        fixed_sum = 0.0
        var_sum = 0.0
        stoppable_events = []
        reducible_events = []

        for _, ev in hist_debits.iterrows():
            ev_dt = parse_date(ev['event_date'])
            amt = float(ev['amount']) if pd.notna(ev['amount']) else 0.0
            curr = str(ev['currency']).strip()
            amt_home = self.converter.convert(amt, curr, home_curr, ev_dt)
            flex = str(ev['flexibility']).lower()
            cat = str(ev['category']).lower()

            if flex in ['stoppable', 'reducible_or_stoppable']:
                stoppable_events.append({'id': ev['event_id'], 'category': cat, 'amount': amt_home})
            if flex in ['reducible', 'reducible_or_stoppable']:
                min_allowed = float(ev['minimum_allowed_amount']) if pd.notna(ev['minimum_allowed_amount']) else (amt_home * 0.5)
                reducible_events.append({'id': ev['event_id'], 'category': cat, 'amount': amt_home, 'min_allowed': min_allowed})

            if cat in ['rent', 'utilities', 'debt_repayment', 'education', 'subscription']:
                if ev_dt:
                    d = ev_dt.day
                    if (req_dt.day <= salary_day and req_dt.day <= d < salary_day) or (req_dt.day > salary_day and (d >= req_dt.day or d < salary_day)):
                        fixed_sum += amt_home
            else:
                var_sum += amt_home

        var_daily = var_sum / 30.0
        pre_payday_debits = fixed_sum + (var_daily * max(1, days_to_payday))

        return next_salary_dt, salary_amt, pre_payday_debits, stoppable_events, reducible_events

    def evaluate_request(self, row):
        req_id = row['request_id']
        u_id = row['user_id']
        req_date_str = str(row['request_date'])
        req_date = parse_date(req_date_str)
        req_type = str(row['request_type'])
        req_amt = float(row['requested_amount'])
        desired_date = parse_date(str(row['desired_completion_date']))
        allow_partial = bool(row['allows_partial_payment'])

        prof = self.profiles[self.profiles['user_id'] == u_id].iloc[0]
        home_curr = str(prof['home_currency']).strip()
        init_bal = float(prof['current_available_balance'])
        min_bal = float(prof['minimum_balance_to_keep'])
        user_methods = [m.strip() for m in str(prof['payment_methods_user_will_consider']).split('|')]
        max_inst_months = float(prof['max_installment_months']) if pd.notna(prof['max_installment_months']) else None

        msg_updates = self.process_messages(u_id)
        next_salary_dt, salary_amt, pre_debits, stoppable_events, reducible_events = self.get_user_recurring_cashflows(u_id, req_date_str, home_curr, msg_updates)

        avail_before_payday = max(0.0, init_bal - pre_debits)
        amount_safe_to_pay = max(0.0, min(req_amt, avail_before_payday - min_bal))

        if amount_safe_to_pay >= req_amt:
            earliest_full_dt = req_date
        else:
            post_payday_bal = avail_before_payday + salary_amt
            if post_payday_bal - req_amt >= min_bal:
                earliest_full_dt = next_salary_dt
            else:
                m = next_salary_dt.month % 12 + 1
                y = next_salary_dt.year + (1 if next_salary_dt.month == 12 else 0)
                subseq_sal_dt = datetime.date(y, m, min(next_salary_dt.day, 28))
                if (post_payday_bal + salary_amt) - req_amt >= min_bal:
                    earliest_full_dt = subseq_sal_dt
                else:
                    earliest_full_dt = None

        earliest_str = format_date(earliest_full_dt)

        options = self.payment_options[self.payment_options['request_id'] == req_id]
        
        affordability_status = "not_affordable"
        recommended_method = "not_recommended"
        payment_plan = "none"
        spending_changes = "none"
        explanation = ""

        # Option A: Full Payment Today (Affordable Now)
        if amount_safe_to_pay >= req_amt and 'full_payment' in user_methods:
            affordability_status = "affordable_now"
            recommended_method = "full_payment"
            payment_plan = f"{req_date_str}:{fmt_amt_plain(req_amt)}"
            earliest_str = req_date_str
            explanation = f"Pay {home_curr} {fmt_amt(req_amt)} today. This leaves at least {home_curr} {fmt_amt(min_bal)} available over the next 90 days."

        # Option B: Installments
        elif 'installments' in user_methods and not options.empty:
            inst_opts = options[options['payment_method'] == 'installments'].copy()
            valid_option = None

            for _, opt in inst_opts.iterrows():
                num_pmts = int(opt['number_of_payments'])
                if max_inst_months and num_pmts > max_inst_months:
                    continue

                pmt_amt = float(opt['payment_amount'])
                first_dt = parse_date(str(opt['first_payment_date']))
                freq = float(opt['payment_frequency_days']) if pd.notna(opt['payment_frequency_days']) else 30.0

                if pmt_amt <= (avail_before_payday - min_bal) or first_dt >= next_salary_dt:
                    last_pmt_dt = first_dt + datetime.timedelta(days=int((num_pmts - 1) * freq))
                    if last_pmt_dt <= desired_date:
                        sched = []
                        for i in range(num_pmts):
                            p_dt = first_dt + datetime.timedelta(days=int(i * freq))
                            sched.append(f"{format_date(p_dt)}:{fmt_amt_plain(pmt_amt)}")
                        
                        plan_str = "|".join(sched)
                        valid_option = (opt['payment_option_id'], plan_str, pmt_amt, num_pmts, first_dt)
                        break

            if valid_option:
                affordability_status = "affordable_with_plan"
                recommended_method = "installments"
                payment_plan = valid_option[1]
                pmt_amt = valid_option[2]
                num_pmts = valid_option[3]
                first_dt_str = format_date(valid_option[4])
                explanation = f"Use {num_pmts} installments of {home_curr} {fmt_amt(pmt_amt)}, starting {first_dt_str}. This leaves at least {home_curr} {fmt_amt(min_bal)} available."

        # Option C: Partial Payment
        if recommended_method == "not_recommended" and allow_partial and 'partial_payment' in user_methods:
            if 0 < amount_safe_to_pay < req_amt and earliest_full_dt and earliest_full_dt <= desired_date:
                affordability_status = "affordable_with_plan"
                recommended_method = "partial_payment"
                rem_amt = req_amt - amount_safe_to_pay
                payment_plan = f"{req_date_str}:{fmt_amt_plain(amount_safe_to_pay)}|{earliest_str}:{fmt_amt_plain(rem_amt)}"
                explanation = f"Pay {home_curr} {fmt_amt(amount_safe_to_pay)} today and the remaining {home_curr} {fmt_amt(rem_amt)} on {earliest_str}. This completes the full request and keeps the {home_curr} {fmt_amt(min_bal)} minimum protected."

        # Option D: Wait
        if recommended_method == "not_recommended" and 'full_payment' in user_methods:
            if earliest_full_dt and earliest_full_dt > req_date and earliest_full_dt <= desired_date:
                affordability_status = "affordable_later"
                recommended_method = "wait"
                payment_plan = f"{earliest_str}:{fmt_amt_plain(req_amt)}"
                explanation = f"Pay {home_curr} {fmt_amt(req_amt)} in full on {earliest_str}. Paying earlier would take the balance below the {home_curr} {fmt_amt(min_bal)} minimum."

        # Option E: Spending Changes Needed
        if recommended_method == "not_recommended" and 'full_payment' in user_methods:
            for ev in stoppable_events:
                if (avail_before_payday + ev['amount']) - min_bal >= req_amt:
                    affordability_status = "affordable_with_plan"
                    recommended_method = "full_payment"
                    payment_plan = f"{req_date_str}:{fmt_amt_plain(req_amt)}"
                    spending_changes = f"stop:{ev['id']}"
                    cat_name = ev['category'].replace('_', ' ')
                    explanation = f"Stop the {cat_name}, then pay {home_curr} {fmt_amt(req_amt)} today. This leaves at least {home_curr} {fmt_amt(min_bal)} available."
                    break

            if recommended_method == "not_recommended":
                for ev in reducible_events:
                    savable = ev['amount'] - ev['min_allowed']
                    if (avail_before_payday + savable) - min_bal >= req_amt:
                        affordability_status = "affordable_with_plan"
                        recommended_method = "full_payment"
                        payment_plan = f"{req_date_str}:{fmt_amt_plain(req_amt)}"
                        spending_changes = f"reduce_to:{ev['id']}:{fmt_amt_plain(ev['min_allowed'])}"
                        cat_name = ev['category'].replace('_', ' ')
                        explanation = f"Reduce the {cat_name} to {home_curr} {fmt_amt(ev['min_allowed'])}, then pay {home_curr} {fmt_amt(req_amt)} today. This leaves at least {home_curr} {fmt_amt(min_bal)} available."
                        break

        # Option F: Not Affordable Fallback
        if recommended_method == "not_recommended":
            affordability_status = "not_affordable"
            payment_plan = "none"
            spending_changes = "none"
            explanation = f"Do not make this payment by {format_date(desired_date)}. None of the available options keeps the {home_curr} {fmt_amt(min_bal)} minimum protected."

        return {
            'request_id': req_id,
            'amount_safe_to_pay': round(amount_safe_to_pay, 2),
            'affordability_status': affordability_status,
            'recommended_payment_method': recommended_method,
            'payment_plan': payment_plan,
            'earliest_date_for_full_payment': earliest_str if earliest_str else "",
            'spending_changes_needed': spending_changes,
            'decision_explanation': explanation
        }

print("FinancialEngine number formatting updated.")
