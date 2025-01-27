import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Function to categorize age
def categorize_age(age):
    if 0 <= age <= 14:
        return "Kids (0-14)"
    elif 15 <= age <= 18:
        return "Teens (15-18)"
    elif 19 <= age <= 45:
        return "Young Adults (19-45)"
    elif age >= 46:
        return "Older Adults (46+)"
    else:
        return "Invalid Age"

# Load Excel file and verify sheet names
excel_file = "Taskdataset.xlsx"
sheet_names = pd.ExcelFile(excel_file).sheet_names
print(f"Sheet names: {sheet_names}")

# Load sheets with the correct sheet names
fam_data = pd.read_excel(excel_file, sheet_name="Fam data")
ind_data = pd.read_excel(excel_file, sheet_name="Ind data")
tv_data = pd.read_excel(excel_file, sheet_name="TV data")

# Debugging: Print column names
print("Columns in Fam data:", fam_data.columns)
print("Columns in Ind data:", ind_data.columns)
print("Columns in TV data:", tv_data.columns)

# Standardize column names to remove any inconsistencies
fam_data.rename(columns=lambda x: x.strip(), inplace=True)
ind_data.rename(columns=lambda x: x.strip(), inplace=True)
tv_data.rename(columns=lambda x: x.strip(), inplace=True)

# Rename "HH Id" in tv_data to "HH ID" to match fam_data and ind_data
tv_data.rename(columns={"HH Id": "HH ID"}, inplace=True)

# Process the ind data sheet for age and validations
ind_data['Ind_DOB'] = pd.to_datetime(ind_data['Ind_DOB'], format='%Y%m%d', errors='coerce')
today = datetime.today()
ind_data['Age'] = ind_data['Ind_DOB'].apply(
    lambda dob: today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day)) if pd.notnull(dob) else None
)
ind_data['Ind_DOB'] = ind_data['Ind_DOB'].dt.strftime('%d-%m-%Y')
ind_data["age_validation"] = ind_data["Age"].apply(
    lambda age: "Date of birth given is wrong" if age is not None and age < 0 else "Date of birth is correct"
)
ind_data['Age_Category'] = ind_data['Age'].apply(categorize_age)

# Merge fam data and ind data using HH ID
fam_ind_merged = pd.merge(fam_data, ind_data, on="HH ID", how="outer")

# Merge the resulting data with tv data using HH ID
final_merged = pd.merge(fam_ind_merged, tv_data, on="HH ID", how="outer")

# Handle duplicates (remove duplicates based on all columns)
final_merged = final_merged.drop_duplicates()

# Save all sheets into a single Excel file
with pd.ExcelWriter("ind_data_validation.xlsx") as writer:
    fam_data.to_excel(writer, sheet_name="fam data", index=False)
    ind_data.to_excel(writer, sheet_name="ind data", index=False)
    tv_data.to_excel(writer, sheet_name="tv data", index=False)
    final_merged.to_excel(writer, sheet_name="Merged Data", index=False)


datap=pd.read_excel("ind_data_validation.xlsx")
family_member_counts = final_merged.groupby('HH ID')['Ind ID'].nunique().reset_index()
family_member_counts.rename(columns={'Ind ID': 'Family Member Count'}, inplace=True)

# Merge the family member counts back into the reshaped data
reshaped_data = final_merged.pivot_table(
    index=['HH ID', 'Fam.county', 'Fam.technician', 'Dwelling Type', 'No. of Rooms',
           'Number of vehicles', 'Financial status'],
    columns='Ind ID',
    values=['Ind Family Relationship', 'Ind gender', 'Age'],
    aggfunc='first'
)

# Flatten the multi-level column index
reshaped_data.columns = ['_'.join(map(str, col)) for col in reshaped_data.columns]
reshaped_data.reset_index(inplace=True)

# Add the family member count to the reshaped data
reshaped_data = reshaped_data.merge(family_member_counts, on='HH ID', how='left')

# Save the reshaped DataFrame to an Excel file
output_path = "reshaped_data_with_counts.xlsx"
reshaped_data.to_excel(output_path, index=False)

print("Data processing complete. Check 'reshaped_data_with_counts.xlsx'.")