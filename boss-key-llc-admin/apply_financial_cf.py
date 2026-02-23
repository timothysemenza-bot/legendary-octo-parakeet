from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Side
from openpyxl.formatting.rule import FormulaRule, ColorScaleRule, CellIsRule

path = r'c:\Users\timot\Documents\Proposal-Microsite\boss-key-llc-admin\Boss-Key-Financial-Architecture.xlsx'
wb = load_workbook(path)

# Common styles
fill_input = PatternFill('solid', fgColor='FFF3CD')      # editable assumptions
fill_selected = PatternFill('solid', fgColor='D4EDDA')   # active scenario column
fill_unselected = PatternFill('solid', fgColor='F1F3F5') # inactive scenario column
fill_warn = PatternFill('solid', fgColor='F8D7DA')       # warning
fill_ok = PatternFill('solid', fgColor='D1ECF1')         # okay
thin = Side(style='thin', color='D7DEEB')
border = Border(left=thin, right=thin, top=thin, bottom=thin)

# 1) Inputs sheet: make interaction obvious
ws = wb['Inputs']

# mark editable assumption cells manually
for r in range(5, 16):
    for c in ['B', 'C']:
        cell = ws[f'{c}{r}']
        cell.fill = fill_input
        cell.border = border

# scenario selector cell
ws['B2'].fill = fill_input
ws['B2'].font = Font(bold=True)
ws['B2'].border = border

# selected scenario highlight on B/C assumption columns
# If Conservative selected, highlight column B; else highlight C
ws.conditional_formatting.add(
    'B5:C15',
    FormulaRule(formula=['AND($B$2="Conservative",COLUMN()=2)'], fill=fill_selected)
)
ws.conditional_formatting.add(
    'B5:C15',
    FormulaRule(formula=['AND($B$2="Moderate",COLUMN()=3)'], fill=fill_selected)
)
ws.conditional_formatting.add(
    'B5:C15',
    FormulaRule(formula=['AND($B$2="Conservative",COLUMN()=3)'], fill=fill_unselected)
)
ws.conditional_formatting.add(
    'B5:C15',
    FormulaRule(formula=['AND($B$2="Moderate",COLUMN()=2)'], fill=fill_unselected)
)

# Selected output guardrails (D column)
# clients (5-6 ideal)
ws.conditional_formatting.add('D5', CellIsRule(operator='notBetween', formula=['5', '6'], fill=fill_warn))
# retainer ($4,500-$6,000 target)
ws.conditional_formatting.add('D6', CellIsRule(operator='notBetween', formula=['4500', '6000'], fill=fill_warn))
# salary range (reasonable planning)
ws.conditional_formatting.add('D10', CellIsRule(operator='notBetween', formula=['120000', '160000'], fill=fill_warn))
# tax reserve between 30%-45%
ws.conditional_formatting.add('D14', CellIsRule(operator='notBetween', formula=['0.30', '0.45'], fill=fill_warn))

# positive cue when in range
ws.conditional_formatting.add('D5', CellIsRule(operator='between', formula=['5', '6'], fill=fill_ok))
ws.conditional_formatting.add('D6', CellIsRule(operator='between', formula=['4500', '6000'], fill=fill_ok))
ws.conditional_formatting.add('D10', CellIsRule(operator='between', formula=['120000', '160000'], fill=fill_ok))
ws.conditional_formatting.add('D14', CellIsRule(operator='between', formula=['0.30', '0.45'], fill=fill_ok))

# 2) Annual model: make key outcomes easy to read
am = wb['Annual_Model']

# Color scale on major dollar outputs
am.conditional_formatting.add(
    'C4:C15',
    ColorScaleRule(start_type='min', start_color='F8D7DA',
                   mid_type='percentile', mid_value=50, mid_color='FFF3CD',
                   end_type='max', end_color='D4EDDA')
)

# Warn if pre-owner comp or S-corp profit go negative
am.conditional_formatting.add('C8', CellIsRule(operator='lessThan', formula=['0'], fill=fill_warn))
am.conditional_formatting.add('C11', CellIsRule(operator='lessThan', formula=['0'], fill=fill_warn))

# 3) Monthly cashflow: flag unhealthy months
mc = wb['Monthly_Cashflow']

# Negative pre-tax month
mc.conditional_formatting.add('F4:F15', CellIsRule(operator='lessThan', formula=['0'], fill=fill_warn))
# Distribution negative (should not happen due formula but keeps visible)
mc.conditional_formatting.add('H4:H15', CellIsRule(operator='lessThan', formula=['0'], fill=fill_warn))
# Buffer falling below 2 months of overhead (rule of thumb)
mc.conditional_formatting.add('I4:I15', CellIsRule(operator='lessThan', formula=['Inputs!D9/6'], fill=fill_warn))
# Healthy buffer high cue
mc.conditional_formatting.add('I4:I15', CellIsRule(operator='greaterThanOrEqual', formula=['Inputs!D9/3'], fill=fill_ok))

# 4) Scenario compare: visually emphasize revenue row
sc = wb['Scenario_Compare']
sc.conditional_formatting.add(
    'B10:D10',
    ColorScaleRule(start_type='min', start_color='F8D7DA',
                   mid_type='percentile', mid_value=50, mid_color='FFF3CD',
                   end_type='max', end_color='D4EDDA')
)

# Add quick legend on Inputs sheet
ws['A22'] = 'How to use:'
ws['A22'].font = Font(bold=True, color='0B1020')
ws['A23'] = 'Yellow = edit assumptions'
ws['A24'] = 'Green = selected scenario / in target range'
ws['A25'] = 'Red = outside target range or risk signal'
ws['A26'] = 'Gray = inactive scenario column'

wb.save(path)
print(path)
