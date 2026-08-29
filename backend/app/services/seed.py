from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import *
from app.services.workflows import (
    next_number,
    transfer,
    change_incharge,
    event,
    ticket_event,
)


def seed(db: Session):
    required_roles = {
        1: ("Administrator", "Complete system access"),
        2: ("Technician", "Service, repair, PM and calibration"),
        3: ("Asset Manager", "Asset lifecycle, contracts and reports"),
        7: ("Employee", "Assigned assets and issue reporting"),
    }
    for role_id, (name, description) in required_roles.items():
        role = db.get(Role, role_id)
        if not role:
            db.add(Role(id=role_id, name=name, description=description))
        else:
            role.name = name
            role.description = description
    db.commit()

    if db.scalar(select(Asset.id).limit(1)):
        # Keep the two supported asset locations consistent in existing databases.
        # Do this before returning so old "GK-I" seeded data is also corrected.
        existing_sites = db.scalars(select(Site)).all()
        by_key = {
            "".join(character for character in site.name.upper() if character.isalnum()): site
            for site in existing_sites
        }
        gk_site = by_key.get("GK1") or by_key.get("GKI")
        if gk_site:
            gk_site.name = "GK-1"
            gk_site.is_active = True
        else:
            gk_site = Site(name="GK-1")
            db.add(gk_site)
        gurgaon_site = by_key.get("GURGAON")
        if gurgaon_site:
            gurgaon_site.name = "Gurgaon"
            gurgaon_site.is_active = True
        else:
            gurgaon_site = Site(name="Gurgaon")
            db.add(gurgaon_site)
        db.flush()
        floor_names = [
            "Basement",
            "Ground Floor",
            "First Floor",
            "Second Floor",
            "Third Floor",
        ]
        for site in [gk_site, gurgaon_site]:
            existing_floor_names = {
                floor.name.casefold()
                for floor in db.scalars(
                    select(Floor).where(Floor.site_id == site.id)
                ).all()
            }
            db.add_all(
                Floor(name=name, site_id=site.id)
                for name in floor_names
                if name.casefold() not in existing_floor_names
            )
        db.commit()
        return

    cats = [
        AssetCategory(name=x)
        for x in ["IT", "Lab Equipment", "Office Equipment", "Furniture"]
    ]
    makes = [
        AssetMake(name=x)
        for x in ["Roche", "Siemens", "Mindray", "Dell", "HP", "Samsung", "Daikin"]
    ]
    sites = [Site(name=x) for x in ["GK-1", "Gurgaon"]]
    depts = [
        Department(name=x)
        for x in [
            "Biochemistry",
            "Hematology",
            "Microbiology",
            "Customer Care",
            "IT",
            "Administration",
        ]
    ]
    db.add_all(cats + makes + sites + depts)
    db.flush()
    floor_names = [
        "Basement",
        "Ground Floor",
        "First Floor",
        "Second Floor",
        "Third Floor",
    ]
    db.add_all(
        Floor(name=floor_name, site_id=site.id)
        for site in sites
        for floor_name in floor_names
    )
    types = []
    for cat, names in zip(
        cats,
        [
            ["Desktop", "Monitor", "Laptop", "Printer", "UPS"],
            ["Chemistry Analyzer", "Centrifuge", "Microscope"],
            ["Air Conditioner", "Microwave"],
            ["Chair", "Workstation", "Cabinet"],
        ],
    ):
        types.extend(AssetType(name=n, category_id=cat.id) for n in names)
    db.add_all(types)
    vendor = Vendor(company_name="Demo Service Partners", phone="1800-000-000")
    db.add(vendor)
    db.flush()
    contact = ServiceContact(
        vendor_id=vendor.id, name="Demo Service Desk", mobile="1800-000-000"
    )
    employees = [
        Employee(employee_code="DBL001", name="IT Manager", department_id=depts[4].id),
        Employee(
            employee_code="DBL002", name="Rahul Sharma", department_id=depts[3].id
        ),
    ]
    db.add_all([contact] + employees)
    db.flush()

    def add(name, cat, type_name, make, **k):
        type_ = next(t for t in types if t.name == type_name)
        asset = Asset(
            asset_code=next_asset_code(db, cat.id),
            public_token=__import__("secrets").token_urlsafe(24),
            asset_name="DEMO — " + name,
            category_id=cat.id,
            asset_type_id=type_.id,
            make_id=make.id,
            current_site_id=sites[0].id,
            staff_incharge_employee_id=employees[0].id,
            primary_service_contact_id=contact.id,
            **k,
        )
        db.add(asset)
        db.flush()
        transfer(db, asset, sites[0].id, None, None, None)
        change_incharge(db, asset, employees[0].id)
        return asset

    monitor = add("Dell Monitor 24 inch", cats[0], "Monitor", makes[3])
    ac = add(
        "Daikin Split AC",
        cats[2],
        "Air Conditioner",
        makes[6],
        pm_required=True,
        pm_period_months=3,
    )
    analyzer = add(
        "Mindray Chemistry Analyzer",
        cats[1],
        "Chemistry Analyzer",
        makes[2],
        calibration_mode="REQUIRED",
        calibration_period_months=12,
    )
    laptop = add(
        "HP Laptop Issued",
        cats[0],
        "Laptop",
        makes[4],
        issued_to_employee_id=employees[1].id,
    )
    repair = add(
        "Dell UPS Under Repair",
        cats[0],
        "UPS",
        makes[3],
        operational_status="UNDER_REPAIR",
    )
    db.add_all(
        [
            PMSchedule(
                asset_id=ac.id,
                frequency_days=90,
                next_due=date.today() - timedelta(days=2),
                provider_vendor_id=vendor.id,
            ),
            CalibrationSchedule(
                asset_id=analyzer.id,
                frequency_days=365,
                next_due=date.today() + timedelta(days=20),
                vendor_id=vendor.id,
            ),
        ]
    )
    contract = ServiceContract(
        contract_number=next_number(db, "contract-2026", "AMC-2026-"),
        contract_type="AMC",
        vendor_id=vendor.id,
        start_date=date.today() - timedelta(days=60),
        end_date=date.today() + timedelta(days=305),
        value=125000,
    )
    db.add(contract)
    db.flush()
    db.add_all(
        [
            ServiceContractAsset(contract_id=contract.id, asset_id=ac.id),
            ServiceContractAsset(contract_id=contract.id, asset_id=analyzer.id),
        ]
    )
    ticket = ServiceTicket(
        ticket_number=next_number(
            db, "ticket-" + str(date.today().year), f"SRV-{date.today().year}-"
        ),
        asset_id=repair.id,
        complaint="Battery backup failed",
        priority="High",
        status="UNDER_REPAIR",
        resolution_path="EXTERNAL",
    )
    db.add(ticket)
    db.flush()
    ticket_event(db, ticket, "REPORTED", "Demo breakdown")
    ticket_event(db, ticket, "ESCALATED", "Vendor contacted")
    db.commit()
