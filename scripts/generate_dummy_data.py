#!/usr/bin/env python3
"""
Synthetic data generator for the Rice Mill BA portfolio (Power BI project).

Writes 13 CSV files to data/raw/. Only the Python standard library is used.
Run from the repository root:   python scripts/generate_dummy_data.py

The data is FAKE. It is built so that the totals match the validation table in
the Power BI guide, and so that the story is visible in the dashboard:
  * paddy buying price steps up about 8% on 1 July 2026  -> price ALERT in July
  * selling prices follow only on 1 September             -> margin squeeze Jul/Aug
  * Red paddy is almost used up on 31 October             -> LOW days of cover
  * a few production batches have yield below 60%         -> low-yield flags
  * unpaid sales and purchases of different ages          -> aging buckets
"""
import csv, os, random
from datetime import date, timedelta
from collections import defaultdict

SEED = 42
START, END = date(2026, 5, 1), date(2026, 10, 31)
DAYS = [START + timedelta(days=i) for i in range((END - START).days + 1)]
ND = len(DAYS)
PADDY_STEP = date(2026, 7, 1)   # buying price rises
SELL_STEP = date(2026, 9, 1)    # selling price follows later

# ---- targets taken from the Power BI guide (validation table) ----
T_PADDY_AMT = 57_373_059
T_RICE_OUT = 326_625
T_RICE_SOLD = 287_655
T_RICE_SALES = 58_508_625
T_BYP_SALES = 1_619_916
T_EXPENSES = 1_180_200
T_RECEIVABLE = 9_304_687
T_PAYABLE = 6_872_030

PADDY_OPEN = {"Samba": 12000, "Nadu": 10000, "Red": 8000}
PADDY_END = {"Samba": 15010, "Nadu": 5330, "Red": 810}
# (paddy, process, product_id, total input kg, number of batches)
BATCH_CFG = [("Samba", "Parboiled", 1, 215000, 48), ("Nadu", "Parboiled", 2, 120000, 27),
             ("Nadu", "Raw", 3, 65000, 15), ("Red", "Parboiled", 4, 70000, 16),
             ("Red", "Raw", 5, 32000, 8)]
PADDY_IN = defaultdict(int)
for p, _, _, kg, _ in BATCH_CFG:
    PADDY_IN[p] += kg
PADDY_BOUGHT = {p: PADDY_END[p] + PADDY_IN[p] - PADDY_OPEN[p] for p in PADDY_OPEN}  # sum = 493,150

PRODUCTS = [(1, "Parboiled Samba", "Packaged"), (2, "Parboiled Nadu", "Packaged"),
            (3, "Kekulu Rice", "Loose"), (4, "Red Rice", "Loose"), (5, "Red Kekulu", "Loose")]
RICE_OPEN = {1: 2500, 2: 2000, 3: 1500, 4: 1000, 5: 500}
SELL_BASE = {1: 232, 2: 205, 3: 190, 4: 215, 5: 195}   # Rs/kg before 1 Sept (scaled later)
PADDY_BASE = {"Samba": 112, "Nadu": 104, "Red": 108}   # Rs/kg before 1 July (scaled later)

FARMERS = ["Kamal Perera", "Sunil Bandara", "Nimal Jayasinghe", "Ranjith Silva", "Piyasena Herath",
           "Gamini Dissanayake", "Wijeratne Banda", "Jayantha Kumara", "Saman Rathnayake", "Upali Gunasekara",
           "Dayananda Wickramasinghe", "Anura Senanayake", "Chandana Ekanayake", "Lalith Seneviratne",
           "Mahinda Karunaratne", "Premasiri Amarasinghe", "Ariyaratne Fernando", "Sarath Weerasinghe",
           "Nandasena Abeysekera", "Tissa Samarasinghe", "Bandula Jayawardena", "Ruwan Pathirana",
           "Somapala Gunawardena", "Kithsiri Madushanka", "Janaka Liyanage"]
SHOPS = ["Perera Stores", "Lanka Provision Stores", "Sathosa Corner Shop", "Nimali Grocery", "Ruwan Super",
         "Sampath Traders", "Ceylon Food Centre", "Chamara Stores", "Dilini Supermarket", "Green Valley Stores",
         "Hemantha Traders", "Isuru Grocery", "Jayasekara Stores", "Kumari Provisions", "Lakmini Stores",
         "Mahaweli Traders", "Nilantha Super", "Oshadi Stores", "Pradeep Grocery", "Rasika Traders",
         "Samanthi Stores", "Thilina Super", "Udaya Provision", "Vijitha Stores", "Wasantha Traders",
         "Yasodha Grocery", "Ama Food City", "Bandara Stores", "Cooray Traders", "Dhanushka Super"]
BYP_BUYERS = ["Rathna Poultry Feeds", "Silva Brick Works", "Nilwala Cattle Feed", "Kandy Oil Mill Agent",
              "Lakshman Hotel Supplies", "Chaminda Farm Supplies"]
TOWNS = ["Polonnaruwa", "Anuradhapura", "Kurunegala", "Hingurakgoda", "Galewela", "Dambulla", "Medirigiriya",
         "Kekirawa", "Mahawa", "Nikaweratiya", "Giriulla", "Wariyapola"]


# ------------------------------------------------------------------ helpers
def egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = egcd(b, a % b)
    return g, y, x - (a // b) * y


def fix_total(items, target_cents):
    """Nudge item prices (cents) so that sum(q * c) equals target_cents exactly."""
    tot = lambda: sum(i["q"] * i["c"] for i in items)
    for _ in range(3_000_000):
        diff = target_cents - tot()
        if abs(diff) < 20000:
            break
        it = random.choice(items)
        d = max(-8, min(8, int(diff / (it["q"] * 6))))
        if d and it["c"] + d > 100:
            it["c"] += d
    R = target_cents - tot()
    small = sorted(items, key=lambda i: i["q"])[:60]
    best = None
    for a in range(len(small)):
        for b in range(a + 1, len(small)):
            if egcd(small[a]["q"], small[b]["q"])[0] == 1:
                s = small[a]["q"] + small[b]["q"]
                if best is None or s < best[0]:
                    best = (s, small[a], small[b])
    _, i, j = best
    g, x, y = egcd(i["q"], j["q"])
    a0, b0 = x * R, y * R
    cand = []
    k0 = round(-a0 / j["q"])
    for k in range(k0 - 400, k0 + 400):
        a, b = a0 + k * j["q"], b0 - k * i["q"]
        cand.append((abs(a) + abs(b), a, b))
    _, a, b = min(cand)
    i["c"] += a
    j["c"] += b
    assert tot() == target_cents and all(it["c"] > 0 for it in items), "fix_total failed"


def rand_day(sundays=False):
    while True:
        d = random.choice(DAYS)
        if sundays or d.weekday() != 6:
            return d


def split_int(total, n, lo=0.55, hi=1.45, minimum=1):
    w = [random.uniform(lo, hi) for _ in range(n)]
    s = sum(w)
    v = [max(minimum, int(round(total * x / s))) for x in w]
    v[-1] += total - sum(v)
    assert v[-1] > 0
    return v


def zipf_weights(n, power=0.8):
    w = [1 / (i + 1) ** power for i in range(n)]
    random.shuffle(w)
    return w


def money(c):  # cents -> '12345.67'
    return f"{c // 100}.{c % 100:02d}"


def write_csv(name, header, rows):
    path = os.path.join(OUT, name + ".csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name}.csv  ({len(rows)} rows)")


def choose_unpaid(recs, target):
    """recs: dicts with key, date, total (cents). Returns {key: unpaid_cents} summing exactly to target."""
    def weight(r):
        age = (END - r["date"]).days
        return 1.0 if age <= 30 else 0.55 if age <= 60 else 0.25
    order = sorted(recs, key=lambda r: random.random() ** (1 / weight(r)), reverse=True)
    unpaid, acc = {}, 0
    for r in order:
        rem = target - acc
        if rem <= 0:
            break
        u = r["total"] if random.random() < 0.55 else int(r["total"] * random.uniform(0.3, 0.8))
        u = min(u, rem) if u >= rem else u
        unpaid[r["key"]] = u
        acc += u
    assert acc == target, "not enough records to carry the unpaid amount"
    return unpaid


def make_payments(recs, unpaid, start_id):
    """Build payment rows for every record: paid part = total - unpaid."""
    rows, pid = [], start_id
    for r in recs:
        paid = r["total"] - unpaid.get(r["key"], 0)
        if paid <= 0:
            continue
        credit = r["key"] in unpaid
        d1 = min(END, r["date"] + timedelta(days=random.randint(0, 20 if credit else 12)))
        if not credit and random.random() < 0.2 and paid > 10000:
            first = int(paid * random.uniform(0.4, 0.7))
            d2 = min(END, d1 + timedelta(days=random.randint(3, 20)))
            parts = [(d1, first), (d2, paid - first)]
        else:
            parts = [(d1, paid)]
        for d, amt in parts:
            m = random.choices(["Cash", "Bank Transfer", "Cheque"], [55, 30, 15])[0]
            rows.append([pid, d.isoformat(), r["sid"], money(amt), m])
            pid += 1
    rows.sort(key=lambda x: (x[1], x[0]))
    for n, r in enumerate(rows, start_id):
        r[0] = n
    return rows


# ------------------------------------------------------------------ generation
def build():
    # ---------- partners
    partners = []
    pid = 1
    farmer_ids = []
    for n in FARMERS:
        partners.append([pid, n, "Farmer", f"07{random.randint(0,8)}{random.randint(1000000,9999999)}",
                         random.choice(TOWNS), 1, 0])
        farmer_ids.append(pid)
        pid += 1
    for k in (1, 6, 12):   # a few farmers also buy by-products
        partners[k][2], partners[k][6] = "Farmer & Buyer", 1
    shop_ids = []
    for n in SHOPS:
        partners.append([pid, n, "Shop", f"07{random.randint(0,8)}{random.randint(1000000,9999999)}",
                         random.choice(["Kurunegala", "Dambulla", "Kandy", "Matale", "Anuradhapura", "Gampaha"]), 0, 1])
        shop_ids.append(pid)
        pid += 1
    byp_ids = []
    for n in BYP_BUYERS:
        partners.append([pid, n, "By-product buyer", f"07{random.randint(0,8)}{random.randint(1000000,9999999)}",
                         random.choice(TOWNS), 0, 1])
        byp_ids.append(pid)
        pid += 1
    byp_pool = byp_ids + [partners[k][0] for k in (1, 6, 12)]
    fw, sw = zipf_weights(len(farmer_ids)), zipf_weights(len(shop_ids), 0.7)

    # ---------- paddy purchases
    raw = []
    premium = {f: random.uniform(-2.5, 2.5) for f in farmer_ids}
    for ptype, (n, kgs) in {"Samba": (90, PADDY_BOUGHT["Samba"]), "Nadu": (80, PADDY_BOUGHT["Nadu"]),
                            "Red": (46, PADDY_BOUGHT["Red"])}.items():
        for kg in split_int(kgs, n, minimum=150):
            d = rand_day()
            f = random.choices(farmer_ids, fw)[0]
            p = PADDY_BASE[ptype] * (1.08 if d >= PADDY_STEP else 1.0) + premium[f] + random.uniform(-1.2, 1.2)
            raw.append({"d": d, "f": f, "t": ptype, "q": kg, "p": p})
    k = T_PADDY_AMT / sum(r["q"] * r["p"] for r in raw)
    for r in raw:
        r["c"] = round(r["p"] * k * 100)
    fix_total(raw, T_PADDY_AMT * 100)
    raw.sort(key=lambda r: (r["d"], r["t"]))
    purchases = [dict(r, id=i) for i, r in enumerate(raw, 1)]
    write_csv("fact_paddy_purchase",
              ["purchase_id", "purchase_date", "partner_id", "paddy_type", "weight_kg", "price_per_kg", "total_amount"],
              [[r["id"], r["d"].isoformat(), r["f"], r["t"], r["q"], money(r["c"]), money(r["q"] * r["c"])]
               for r in purchases])

    # ---------- production batches (placed so paddy stock never goes negative)
    for attempt in range(200):
        stock = {p: [PADDY_OPEN[p]] * ND for p in PADDY_OPEN}
        for r in purchases:
            i = DAYS.index(r["d"])
            for j in range(i, ND):
                stock[r["t"]][j] += r["q"]
        batches = []
        for ptype, proc, prod, tot, n in BATCH_CFG:
            for kg in split_int(tot, n, 0.6, 1.4, 500):
                batches.append({"t": ptype, "proc": proc, "prod": prod, "q": kg})
        batches.sort(key=lambda b: -b["q"])
        ok = True
        for b in batches:
            s = stock[b["t"]]
            suf = [0] * ND
            m = 10 ** 9
            for j in range(ND - 1, -1, -1):
                m = min(m, s[j])
                suf[j] = m
            feas = [j for j in range(ND) if suf[j] >= b["q"] and DAYS[j].weekday() != 6]
            if not feas:
                ok = False
                break
            j = random.choice(feas)
            b["d"] = DAYS[j]
            for x in range(j, ND):
                s[x] -= b["q"]
        if ok:
            break
    else:
        raise RuntimeError("could not place batches")
    # yields
    for b in batches:
        mean = 0.665 if b["proc"] == "Parboiled" else 0.625
        b["y"] = random.gauss(mean, 0.012)
    for b in random.sample(batches, 7):
        b["y"] = random.uniform(0.50, 0.58)
    outs = [b["q"] * b["y"] for b in batches]
    s = T_RICE_OUT / sum(outs)
    for b, o in zip(batches, outs):
        b["o"] = int(round(o * s))
    big = max(batches, key=lambda b: b["q"])
    big["o"] += T_RICE_OUT - sum(b["o"] for b in batches)
    batches.sort(key=lambda b: (b["d"], b["t"], b["proc"]))
    brows = []
    for i, b in enumerate(batches, 1):
        if random.random() < 0.12:
            h = pl = br = ""
        else:
            h = int(b["q"] * random.uniform(0.19, 0.21))
            pl = int(b["q"] * random.uniform(0.03, 0.04))
            br = int(b["q"] * random.uniform(0.04, 0.06))
        b["id"] = i
        brows.append([i, b["d"].isoformat(), b["t"], b["proc"], b["prod"], b["q"], b["o"], h, pl, br])
    write_csv("fact_production_batch",
              ["batch_id", "batch_date", "paddy_type", "process_type", "product_id", "input_kg", "output_kg",
               "husk_kg", "polisher_kg", "broken_kg"], brows)

    # ---------- rice sales (events per product, limited by running rice stock)
    out_p = defaultdict(int)
    for b in batches:
        out_p[b["prod"]] += b["o"]
    ratio = T_RICE_SOLD / (sum(RICE_OPEN.values()) + T_RICE_OUT)
    sold_t = {p: int(round(ratio * (RICE_OPEN[p] + out_p[p]) / 5) * 5) for p in (1, 2, 3, 4)}
    sold_t[5] = T_RICE_SOLD - sum(sold_t.values())
    events = []
    for prod in range(1, 6):
        st = [RICE_OPEN[prod]] * ND
        for b in batches:
            if b["prod"] == prod:
                for j in range(DAYS.index(b["d"]), ND):
                    st[j] += b["o"]
        remaining = sold_t[prod]
        packaged = prod in (1, 2)
        while remaining > 0:
            suf, m = [0] * ND, 10 ** 9
            for j in range(ND - 1, -1, -1):
                m = min(m, st[j])
                suf[j] = m
            feas_max = max(suf[j] for j in range(ND) if DAYS[j].weekday() != 6)
            if packaged:
                size = random.choices([5, 10, 25], [25, 30, 45])[0]
                packs = random.randint(*{5: (4, 40), 10: (3, 30), 25: (2, 24)}[size])
                qty = size * packs
                cap = min(remaining, feas_max)
                if qty > cap:
                    size = 25 if cap >= 25 else 10 if cap >= 10 else 5
                    packs = max(1, cap // size)
                    qty = size * packs
                    if qty > cap:
                        raise RuntimeError("stock timing problem")
            else:
                size, packs = None, None
                qty = min(random.randint(30, 700), remaining, feas_max)
                if qty <= 0:
                    raise RuntimeError("stock timing problem")
            cands = [j for j in range(ND) if suf[j] >= qty and DAYS[j].weekday() != 6]
            j = random.choice(cands)
            for x in range(j, ND):
                st[x] -= qty
            events.append({"d": DAYS[j], "prod": prod, "q": qty, "size": size, "packs": packs})
            remaining -= qty
    # group events into sales (up to 3 different products per sale)
    by_day = defaultdict(list)
    for e in events:
        by_day[e["d"]].append(e)
    sales = []
    for d in sorted(by_day):
        evs = by_day[d]
        random.shuffle(evs)
        while evs:
            take, rest, seen = [], [], set()
            limit = random.choice([1, 2, 2, 3])
            for e in evs:
                if len(take) < limit and e["prod"] not in seen:
                    take.append(e)
                    seen.add(e["prod"])
                else:
                    rest.append(e)
            evs = rest
            sales.append({"d": d, "p": random.choices(shop_ids, sw)[0], "lines": take})
    discount = {s: random.uniform(-3, 3) for s in shop_ids}
    lines = []
    for sid, s in enumerate(sales, 1):
        s["id"] = sid
        for e in s["lines"]:
            prem = {5: 4, 10: 2, 25: 0, None: 0}[e["size"]]
            p = SELL_BASE[e["prod"]] * (1.04 if s["d"] >= SELL_STEP else 1.0) + prem + discount[s["p"]] + random.uniform(-1.5, 1.5)
            lines.append({"sid": sid, "q": e["q"], "e": e, "p": p, "d": s["d"]})
    k = T_RICE_SALES / sum(l["q"] * l["p"] for l in lines)
    for l in lines:
        l["c"] = round(l["p"] * k * 100)
    fix_total(lines, T_RICE_SALES * 100)
    lrows = []
    for n, l in enumerate(lines, 1):
        e = l["e"]
        lrows.append([n, l["sid"], e["prod"], e["size"] if e["size"] else "", e["packs"] if e["packs"] else "",
                      l["q"], money(l["c"]), money(l["q"] * l["c"])])
    tot_sale = defaultdict(int)
    for l in lines:
        tot_sale[l["sid"]] += l["q"] * l["c"]
    srows = [[s["id"], s["d"].isoformat(), s["p"], money(tot_sale[s["id"]])] for s in sales]
    write_csv("fact_rice_sale", ["sale_id", "sale_date", "partner_id", "total_amount"], srows)
    write_csv("fact_rice_sale_line", ["line_id", "sale_id", "product_id", "pack_size_kg", "packs", "quantity_kg",
                                      "price_per_kg", "line_total"], lrows)

    # ---------- by-product sales
    bev = []
    for typ, n, lo, hi, base in [("Husk", 22, 1500, 4000, 8), ("Polisher", 28, 250, 800, 40),
                                 ("Broken Rice", 20, 150, 450, 130)]:
        for _ in range(n):
            d = rand_day()
            bev.append({"d": d, "t": typ, "q": random.randint(lo, hi), "p": base + random.uniform(-0.1, 0.1) * base,
                        "pid": random.choice(byp_pool)})
    k = T_BYP_SALES / sum(b["q"] * b["p"] for b in bev)
    for b in bev:
        b["c"] = round(b["p"] * k * 100)
    fix_total(bev, T_BYP_SALES * 100)
    bev.sort(key=lambda b: (b["d"], b["t"]))
    for i, b in enumerate(bev, 1):
        b["id"] = i
    write_csv("fact_byproduct_sale", ["sale_id", "sale_date", "partner_id", "byproduct_type", "quantity_kg",
                                      "price_per_kg", "total_amount"],
              [[b["id"], b["d"].isoformat(), b["pid"], b["t"], b["q"], money(b["c"]), money(b["q"] * b["c"])]
               for b in bev])

    # ---------- payments
    prec = [{"key": ("P", r["id"]), "sid": r["id"], "date": r["d"], "total": r["q"] * r["c"]} for r in purchases]
    pay_unpaid = choose_unpaid(prec, T_PAYABLE * 100)
    write_csv("fact_payment_paddy", ["payment_id", "payment_date", "purchase_id", "amount", "method"],
              make_payments(prec, pay_unpaid, 1))
    rrec = [{"key": ("R", s["id"]), "sid": s["id"], "date": s["d"], "total": tot_sale[s["id"]]} for s in sales]
    brec = [{"key": ("B", b["id"]), "sid": b["id"], "date": b["d"], "total": b["q"] * b["c"]} for b in bev]
    rec_unpaid = choose_unpaid(rrec + brec, T_RECEIVABLE * 100)
    write_csv("fact_payment_rice", ["payment_id", "payment_date", "sale_id", "amount", "method"],
              make_payments(rrec, rec_unpaid, 1))
    write_csv("fact_payment_byproduct", ["payment_id", "payment_date", "sale_id", "amount", "method"],
              make_payments(brec, rec_unpaid, 1))

    # ---------- expenses (amounts in whole rupees, total fixed)
    ex = []
    for m in range(5, 11):
        ex.append([date(2026, m, 28), "Electricity", random.randint(85, 125) * 1000, f"Electricity bill {date(2026, m, 1):%b %Y}"])
    for _ in range(5):
        ex.append([rand_day(), "Machine Maintenance", random.randint(20, 60) * 1000, "Machine servicing / spare parts"])
    for m in (5, 7, 9):
        ex.append([date(2026, m, 15), "Packet Printing", random.randint(15, 25) * 1000, "Printed packets (5/10/25 kg)"])
    for _ in range(8):
        ex.append([rand_day(), "Hired Transport", random.randint(15, 35) * 1000, "Hired lorry for delivery run"])
    for _ in range(4):
        ex.append([rand_day(), "Other", random.randint(8, 25) * 1000, "Miscellaneous"])
    f = T_EXPENSES / sum(e[2] for e in ex)          # scale all rows, round to Rs 100,
    for e in ex:                                      # then let the last row absorb the rounding
        e[2] = int(round(e[2] * f / 100) * 100)
    ex[-1][2] += T_EXPENSES - sum(e[2] for e in ex)
    assert 5000 <= ex[-1][2] <= 60000, ex[-1]
    ex.sort(key=lambda e: e[0])
    write_csv("fact_expense", ["expense_id", "expense_date", "category", "amount", "description"],
              [[i, e[0].isoformat(), e[1], f"{e[2]}.00", e[3]] for i, e in enumerate(ex, 1)])

    # ---------- dimensions and opening stock
    write_csv("dim_partner", ["partner_id", "partner_name", "partner_type", "phone", "town", "is_supplier", "is_customer"],
              partners)
    write_csv("dim_product", ["product_id", "product_name", "sale_form"], [list(p) for p in PRODUCTS])
    write_csv("opening_paddy", ["paddy_type", "quantity_kg"], [[k, v] for k, v in PADDY_OPEN.items()])
    write_csv("opening_rice", ["product_id", "quantity_kg"], [[k, v] for k, v in RICE_OPEN.items()])

    return dict(purchases=purchases, batches=batches, lines=lines, sales=sales, bev=bev, tot_sale=tot_sale,
                pay_unpaid=pay_unpaid, rec_unpaid=rec_unpaid, prec=prec, rrec=rrec, brec=brec, ex=ex)


def validate(D):
    P, B = D["purchases"], D["batches"]
    bought = sum(r["q"] for r in P)
    paid_amt = sum(r["q"] * r["c"] for r in P)
    rice_sales = sum(l["q"] * l["c"] for l in D["lines"])
    byp = sum(b["q"] * b["c"] for b in D["bev"])
    exp = sum(e[2] for e in D["ex"])
    inp, out = sum(b["q"] for b in B), sum(b["o"] for b in B)
    sold = sum(l["q"] for l in D["lines"])
    print("\n=== Validation against the guide (should all say OK) ===")
    rows = [("Paddy Bought Kg", bought, 493150), ("Paddy Purchase Amount", paid_amt / 100, T_PADDY_AMT),
            ("Batch Input Kg", inp, 502000), ("Rice Output Kg", out, T_RICE_OUT), ("Rice Sold Kg", sold, T_RICE_SOLD),
            ("Rice Sales", rice_sales / 100, T_RICE_SALES), ("By-product Sales", byp / 100, T_BYP_SALES),
            ("Expenses", exp, T_EXPENSES), ("Total Sales", (rice_sales + byp) / 100, 60128541),
            ("Estimated Profit", (rice_sales + byp) / 100 - paid_amt / 100 - exp, 1575282),
            ("Total Receivable", sum(D["rec_unpaid"].values()) / 100, T_RECEIVABLE),
            ("Payable to Farmers", sum(D["pay_unpaid"].values()) / 100, T_PAYABLE)]
    for n, a, e in rows:
        print(f"  {n:24s} {a:>14,.0f} {e:>14,}   {'OK' if abs(a - e) < 0.5 else 'MISMATCH'}")
    print("  Paddy stock 31 Oct:", {t: PADDY_OPEN[t] + sum(r["q"] for r in P if r["t"] == t)
                                   - sum(b["q"] for b in B if b["t"] == t) for t in PADDY_OPEN})
    print("  Low-yield batches (<60%):", sum(1 for b in B if b["o"] / b["q"] < 0.6), "of", len(B))
    print("\n  Avg paddy price by month (Rs/kg) and change:")
    prev = None
    for m in range(5, 11):
        rs = [r for r in P if r["d"].month == m]
        a = sum(r["q"] * r["c"] for r in rs) / sum(r["q"] for r in rs) / 100
        ch = f"{(a / prev - 1) * 100:+.1f}%" if prev else "-"
        print(f"    {m:02d}/2026  {a:7.2f}  {ch}  {'ALERT' if prev and abs(a / prev - 1) >= 0.05 else ''}")
        prev = a
    print("\n  Margin per kg by month (selling price - paddy price / yield):")
    for m in range(5, 11):
        rs = [r for r in P if r["d"].month == m]
        pa = sum(r["q"] * r["c"] for r in rs) / sum(r["q"] for r in rs) / 100
        bs = [b for b in B if b["d"].month == m]
        y = sum(b["o"] for b in bs) / sum(b["q"] for b in bs)
        ls = [l for l in D["lines"] if l["d"].month == m]
        sp = sum(l["q"] * l["c"] for l in ls) / sum(l["q"] for l in ls) / 100
        print(f"    {m:02d}/2026  sell {sp:6.1f}  paddy {pa:6.1f}  yield {y:.3f}  margin/kg {sp - pa / y:6.1f}")
    age = defaultdict(int)
    for r in D["rrec"]:
        u = D["rec_unpaid"].get(r["key"], 0)
        a = (END - r["date"]).days
        age["0-30" if a <= 30 else "31-60" if a <= 60 else "60+"] += u
    print("\n  Rice receivable by age bucket (Rs):", {k: f"{v / 100:,.0f}" for k, v in age.items()})


if __name__ == "__main__":
    random.seed(SEED)
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw")
    os.makedirs(OUT, exist_ok=True)
    print("Writing CSV files to", os.path.normpath(OUT))
    validate(build())
