"""KPI mensuels boutique café. stdlib uniquement : python3 monthly_kpis.py

Nettoyage appliqué : doublons d'order_id supprimés, remboursements (R*) isolés.
Normalisation par jour : indispensable tant qu'un mois est en cours.
"""
import csv, collections, calendar, datetime as dt

ORDERS, ITEMS, CUSTOMERS = 'orders.csv', 'order_items.csv', 'customers.csv'

def load(p): return list(csv.DictReader(open(p)))

def clean(orders):
    """Dédoublonne par order_id, sépare ventes et remboursements."""
    seen, sales, refunds = set(), [], []
    for o in orders:
        if o['order_id'] in seen: continue
        seen.add(o['order_id'])
        (refunds if float(o['amount_eur']) < 0 else sales).append(o)
    return sales, refunds, len(orders) - len(seen)

def days_in(month, last_date):
    """Jours écoulés dans le mois : mois complet, ou jours observés si en cours."""
    y, m = int(month[:4]), int(month[5:7])
    full = calendar.monthrange(y, m)[1]
    return last_date.day if (y, m) == (last_date.year, last_date.month) else full

def main():
    orders, items, customers = load(ORDERS), load(ITEMS), load(CUSTOMERS)
    cust = {c['customer_id']: c for c in customers}
    sales, refunds, dups = clean(orders)
    last = max(dt.date.fromisoformat(o['order_date']) for o in orders)

    first = {}
    for o in sorted(sales, key=lambda o: o['order_date']):
        first.setdefault(o['customer_id'], o['order_date'])

    months = sorted({o['order_date'][:7] for o in orders})
    D = {m: days_in(m, last) for m in months}

    ca = collections.Counter(); n = collections.Counter(); rb = collections.Counter()
    ca_new = collections.Counter(); n_new = collections.Counter(); promo = collections.Counter()
    for o in sales:
        m = o['order_date'][:7]; a = float(o['amount_eur'])
        ca[m] += a; n[m] += 1
        if o['promo_code'].strip(): promo[m] += 1
        if first.get(o['customer_id']) == o['order_date']:
            ca_new[m] += a; n_new[m] += 1
    for o in refunds: rb[o['order_date'][:7]] += -float(o['amount_eur'])

    print(f"Données jusqu'au {last} | {dups} doublons retirés | {len(refunds)} remboursements\n")
    hdr = ('mois', 'jours', 'CA brut', 'remb.', 'CA net', 'EUR/j', 'cmd', 'cmd/j',
           'panier', '%nouv.', '%promo', 'actifs/j')
    print(''.join(f'{h:>10}' for h in hdr))
    for m in months:
        act = len({o['customer_id'] for o in sales if o['order_date'][:7] == m and o['customer_id']})
        flag = '  <- mois incomplet' if D[m] < calendar.monthrange(int(m[:4]), int(m[5:7]))[1] else ''
        print(f'{m:>10}{D[m]:10d}{ca[m]:10.0f}{rb[m]:10.0f}{ca[m]-rb[m]:10.0f}'
              f'{ca[m]/D[m]:10.1f}{n[m]:10d}{n[m]/D[m]:10.2f}{ca[m]/n[m]:10.2f}'
              f'{100*ca_new[m]/ca[m]:9.0f}%{100*promo[m]/n[m]:9.0f}%{act/D[m]:10.2f}{flag}')

    print('\nAcquisition vs rétention (EUR/jour)')
    print(f"{'mois':>10}{'nouveaux':>12}{'récurrents':>12}")
    for m in months:
        print(f'{m:>10}{ca_new[m]/D[m]:12.1f}{(ca[m]-ca_new[m])/D[m]:12.1f}')

    # ponytail: taux de conversion absent — aucune donnée de trafic/sessions.
    print('\nTaux de conversion : non calculable, il manque les sessions/visites.'
          '\n  -> exporter sessions par mois, puis conversion = commandes / sessions.')

def demo():
    """Check minimal : la logique de nettoyage et de jours écoulés."""
    o = [{'order_id': 'A', 'amount_eur': '10', 'order_date': '2026-01-01'},
         {'order_id': 'A', 'amount_eur': '10', 'order_date': '2026-01-01'},
         {'order_id': 'R1', 'amount_eur': '-5', 'order_date': '2026-01-02'}]
    s, r, d = clean(o)
    assert (len(s), len(r), d) == (1, 1, 1), (s, r, d)
    assert days_in('2026-06', dt.date(2026, 6, 14)) == 14
    assert days_in('2026-05', dt.date(2026, 6, 14)) == 31
    print('ok')

if __name__ == '__main__':
    import sys
    demo() if '--check' in sys.argv else main()
