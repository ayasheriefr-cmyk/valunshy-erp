from decimal import Decimal
import datetime

def test_logic():
    processed_products = [] 
    goal_profit = Decimal('200000')
    goal_months = 3
    net_profit = Decimal('89129')
    efficiency_data = [
        {'stage': 'Stage 1', 'avg_duration': '0:10:00', 'count': 5},
        {'stage': 'Stage 2', 'avg_duration': '0:05:00', 'count': 5}
    ]

    goal_results = {
        'target': goal_profit,
        'months': goal_months,
        'items_needed': [],
        'labor_needed': []
    }
    
    total_historical_profit = sum([p[1]['total_profit'] for p in processed_products])
    monthly_target = goal_profit / Decimal(goal_months)
    target_products = processed_products
    
    if not target_products or total_historical_profit <= 0:
        target_products = [
            ("خاتم ذهب عيار 18 (موديل إيطالي)", {
                'count': 15, 'avg_profit': Decimal('650'), 'total_profit': Decimal('9750'),
                'avg_weight': Decimal('3.5'), 'avg_revenue': Decimal('8500')
            }),
            ("سلسلة ذهب كليوباترا 21", {
                'count': 8, 'avg_profit': Decimal('1450'), 'total_profit': Decimal('11600'),
                'avg_weight': Decimal('12.5'), 'avg_revenue': Decimal('32000')
            }),
            ("غويشة ذهب سادة 21", {
                'count': 12, 'avg_profit': Decimal('2100'), 'total_profit': Decimal('25200'),
                'avg_weight': Decimal('22.0'), 'avg_revenue': Decimal('56000')
            }),
            ("حلق ذهب فصوص 18", {
                'count': 20, 'avg_profit': Decimal('450'), 'total_profit': Decimal('9000'),
                'avg_weight': Decimal('4.2'), 'avg_revenue': Decimal('9200')
            })
        ]
        total_historical_profit = sum([p[1]['total_profit'] for p in target_products])
    
    current_monthly_profit = total_historical_profit if total_historical_profit > 0 else Decimal('1')
    growth_factor = monthly_target / current_monthly_profit

    if len(processed_products) == 1 and growth_factor > 100:
         growth_factor = 10 

    for name, stats in target_products:
        if stats['total_profit'] <= 0: continue
        target_units_per_month = int(Decimal(stats['count']) * growth_factor)
        total_units_needed = target_units_per_month * goal_months
        expected_profit = total_units_needed * stats['avg_profit']
        if total_units_needed > 0:
            goal_results['items_needed'].append({
                'product_name': name,
                'required_units': total_units_needed,
                'monthly_rate': target_units_per_month,
                'daily_rate': round(target_units_per_month / 26, 1),
                'total_profit': expected_profit,
                'total_weight': total_units_needed * stats.get('avg_weight', Decimal('3.5')),
                'total_value': total_units_needed * stats.get('avg_revenue', Decimal('7500'))
            })

    goal_results['items_needed'].sort(key=lambda x: x['total_profit'], reverse=True)
    total_ops_needed = sum([it['required_units'] for it in goal_results['items_needed']])
    
    for stage in efficiency_data:
        h, m, s = 0, 0, 0
        try:
            parts = stage['avg_duration'].split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
            elif len(parts) == 2:
                m, s = map(int, parts)
        except: pass
        avg_seconds = h*3600 + m*60 + s
        total_seconds_needed = total_ops_needed * avg_seconds
        if total_seconds_needed > 0:
            goal_results['labor_needed'].append({
                'stage': stage['stage'],
                'hours': round(total_seconds_needed / 3600, 1),
                'total_ops': total_ops_needed
            })
    return goal_results

results = test_logic()
print("Success!")
for item in results['items_needed']:
    print(f"Item: {item['product_name']}, Units: {item['required_units']}")
for labor in results['labor_needed']:
    print(f"Stage: {labor['stage']}, Hours: {labor['hours']}")
