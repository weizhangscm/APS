"""
Initialize Demo Data Script (English Version)
Create work centers, resources, products, routings and production orders
"""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app import models


def create_demo_data(force=False):
    """Create demo data"""
    from app.database import engine, Base

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_data = False
        try:
            existing_data = db.query(models.WorkCenter).count() > 0
        except:
            pass

        if existing_data:
            if not force:
                print("Data already exists")
                print("Use --force parameter to force recreation of data")
                return
            else:
                print("Force mode: Rebuilding database structure...")
                db.close()
                # Drop all tables and rebuild
                Base.metadata.drop_all(bind=engine)
                Base.metadata.create_all(bind=engine)
                db = SessionLocal()
                print("Database structure rebuilt")
        else:
            # Ensure all tables exist
            Base.metadata.create_all(bind=engine)

        print("Starting to create demo data...")

        # ==================== Work Centers ====================
        work_centers = [
            models.WorkCenter(code="WC001", name="Machining Workshop", description="CNC machining, turning, milling"),
            models.WorkCenter(code="WC002", name="Sheet Metal Workshop", description="Cutting, bending, welding"),
            models.WorkCenter(code="WC003", name="Assembly Workshop", description="Product assembly and testing"),
            models.WorkCenter(code="WC004", name="Electronics Workshop", description="PCB assembly and electronic component mounting"),
            models.WorkCenter(code="WC005", name="Quality Control", description="Quality inspection and testing"),
        ]

        for wc in work_centers:
            db.add(wc)
        db.commit()

        print(f"Created {len(work_centers)} work centers")

        # ==================== Resources ====================
        resources = [
            # Machining Workshop resources
            models.Resource(code="CNC-1", name="CNC Machine-1", work_center_id=work_centers[0].id, capacity_per_day=8.0),
            models.Resource(code="CNC-2", name="CNC Machine-2", work_center_id=work_centers[0].id, capacity_per_day=8.0),
            models.Resource(code="LATHE-1", name="Lathe-1", work_center_id=work_centers[0].id, capacity_per_day=8.0),
            models.Resource(code="MILL-1", name="Milling Machine-1", work_center_id=work_centers[0].id, capacity_per_day=8.0),

            # Sheet Metal Workshop resources
            models.Resource(code="PRESS-1", name="Press Machine-1", work_center_id=work_centers[1].id, capacity_per_day=8.0),
            models.Resource(code="BEND-1", name="Bending Machine-1", work_center_id=work_centers[1].id, capacity_per_day=8.0),
            models.Resource(code="WELD-1", name="Welding Station-1", work_center_id=work_centers[1].id, capacity_per_day=8.0),

            # Assembly Workshop resources
            models.Resource(code="ASM-1", name="Assembly Station-1", work_center_id=work_centers[2].id, capacity_per_day=16.0),
            models.Resource(code="ASM-2", name="Assembly Station-2", work_center_id=work_centers[2].id, capacity_per_day=16.0),

            # Electronics Workshop resources
            models.Resource(code="SMT-1", name="SMT Line-1", work_center_id=work_centers[3].id, capacity_per_day=8.0),
            models.Resource(code="TEST-1", name="Test Station-1", work_center_id=work_centers[3].id, capacity_per_day=8.0),

            # Quality Control resources
            models.Resource(code="QC-1", name="Quality Control Station-1", work_center_id=work_centers[4].id, capacity_per_day=24.0),
        ]

        for res in resources:
            db.add(res)
        db.commit()

        print(f"Created {len(resources)} resources")

        # ==================== Products ====================
        products = [
            models.Product(code="MAT001", name="Precision Gear", description="High-precision gear component", unit="PCS"),
            models.Product(code="MAT002", name="Motor Housing", description="Aluminum motor housing", unit="PCS"),
            models.Product(code="MAT003", name="Sensor Module", description="Electronic sensor module", unit="PCS"),
            models.Product(code="MAT004", name="Control Board", description="PCB control board", unit="PCS"),
            models.Product(code="MAT005", name="Bearing Housing", description="Precision bearing housing", unit="PCS"),
            models.Product(code="MAT006", name="Connector", description="Electrical connector", unit="PCS"),
            models.Product(code="MAT007", name="Heat Sink", description="Aluminum heat sink", unit="PCS"),
            models.Product(code="MAT008", name="Enclosure", description="Metal enclosure", unit="PCS"),
            models.Product(code="MAT009", name="Power Module", description="Power supply module", unit="PCS"),
            models.Product(code="MAT010", name="Display Panel", description="LCD display panel", unit="PCS"),
        ]

        for prod in products:
            db.add(prod)
        db.commit()

        print(f"Created {len(products)} products (materials)")

        # ==================== Routings ====================
        # Product to routing mapping
        product_routing_map = {
            0: 0,  # Precision Gear -> Machining type
            1: 1,  # Motor Housing -> Sheet metal type
            2: 3,  # Sensor Module -> Precision components type
            3: 2,  # Control Board -> Electronics assembly type
            4: 0,  # Bearing Housing -> Machining type
            5: 3,  # Connector -> Precision components type
            6: 1,  # Heat Sink -> Sheet metal type
            7: 1,  # Enclosure -> Sheet metal type
            8: 2,  # Power Module -> Electronics assembly type
            9: 2,  # Display Panel -> Electronics assembly type
        }

        # Routing templates for different types
        routing_templates = [
            # 0: Machining type
            [
                {"name": "Rough Machining", "work_center_id": work_centers[0].id, "setup_time": 0.5, "run_time_per_unit": 0.2},
                {"name": "Precision Machining", "work_center_id": work_centers[0].id, "setup_time": 0.3, "run_time_per_unit": 0.3},
                {"name": "Quality Check", "work_center_id": work_centers[4].id, "setup_time": 0.1, "run_time_per_unit": 0.05},
            ],
            # 1: Sheet metal type
            [
                {"name": "Cutting", "work_center_id": work_centers[1].id, "setup_time": 0.2, "run_time_per_unit": 0.1},
                {"name": "Bending", "work_center_id": work_centers[1].id, "setup_time": 0.3, "run_time_per_unit": 0.15},
                {"name": "Welding", "work_center_id": work_centers[1].id, "setup_time": 0.4, "run_time_per_unit": 0.2},
                {"name": "Surface Treatment", "work_center_id": work_centers[2].id, "setup_time": 0.1, "run_time_per_unit": 0.05},
            ],
            # 2: Electronics assembly type
            [
                {"name": "Component Placement", "work_center_id": work_centers[3].id, "setup_time": 0.5, "run_time_per_unit": 0.1},
                {"name": "Soldering", "work_center_id": work_centers[3].id, "setup_time": 0.2, "run_time_per_unit": 0.05},
                {"name": "Testing", "work_center_id": work_centers[4].id, "setup_time": 0.1, "run_time_per_unit": 0.03},
                {"name": "Final Assembly", "work_center_id": work_centers[2].id, "setup_time": 0.3, "run_time_per_unit": 0.1},
            ],
            # 3: Precision components type
            [
                {"name": "Precision Machining", "work_center_id": work_centers[0].id, "setup_time": 0.4, "run_time_per_unit": 0.25},
                {"name": "Assembly", "work_center_id": work_centers[2].id, "setup_time": 0.2, "run_time_per_unit": 0.08},
                {"name": "Calibration", "work_center_id": work_centers[4].id, "setup_time": 0.1, "run_time_per_unit": 0.04},
            ],
        ]

        routings = []
        for i, prod in enumerate(products):
            routing_index = product_routing_map.get(i, 0)
            template = routing_templates[routing_index]

            routing = models.Routing(
                code=f"RT{str(i+1).zfill(3)}",
                name=f"{prod.name} Standard Process",
                product_id=prod.id,
                version="1.0",
                is_active=1
            )
            db.add(routing)
            db.commit()

            # Add operations
            for seq, op_template in enumerate(template, 1):
                operation = models.RoutingOperation(
                    routing_id=routing.id,
                    sequence=seq,
                    name=op_template["name"],
                    work_center_id=op_template["work_center_id"],
                    setup_time=op_template["setup_time"],
                    run_time_per_unit=op_template["run_time_per_unit"],
                    description=f"Operation {seq} for {prod.name}"
                )
                db.add(operation)

            routings.append(routing)

        db.commit()
        print(f"Created {len(routings)} routings and operations")

        # ==================== Orders (Planned Orders + Production Orders) ====================

        # Planned Orders (35) - Pending Schedule
        planned_orders_data = []
        for i in range(35):
            # Randomly select product
            product = random.choice(products)

            # Random quantity (50-500)
            quantity = random.randint(50, 500)

            # Due date: 5-30 days later
            due_date = datetime.now() + timedelta(days=random.randint(5, 30))

            # Priority 1-10
            priority = random.randint(1, 10)

            planned_orders_data.append({
                "order_number": f"PL{str(i+1).zfill(3)}",
                "product_id": product.id,
                "quantity": quantity,
                "due_date": due_date,
                "priority": priority,
                "description": f"{product.name} Planned Order"
            })

        # Production Orders (15) - Confirmed times
        production_orders_data = []
        for i in range(15):
            # Randomly select product
            product = random.choice(products)

            # Random quantity (50-300)
            quantity = random.randint(50, 300)

            # Due date: 2-15 days later
            due_date = datetime.now() + timedelta(days=random.randint(2, 15))

            # Confirmed start time: 1-7 days later
            confirmed_start = datetime.now() + timedelta(days=random.randint(1, 7))

            # Confirmed end time: 1-5 days after start
            confirmed_end = confirmed_start + timedelta(days=random.randint(1, 5))

            # Priority 1-5 (Production orders usually have higher priority)
            priority = random.randint(1, 5)

            production_orders_data.append({
                "order_number": f"PR{str(i+1).zfill(3)}",
                "product_id": product.id,
                "quantity": quantity,
                "due_date": due_date,
                "confirmed_start": confirmed_start,
                "confirmed_end": confirmed_end,
                "priority": priority,
                "description": f"{product.name} Production Order (Released)"
            })

        # Merge and sort by due date
        all_orders_data = planned_orders_data + production_orders_data
        all_orders_data.sort(key=lambda x: x["due_date"])

        # Create orders
        orders = []
        for order_data in all_orders_data:
            order = models.ProductionOrder(
                order_number=order_data["order_number"],
                order_type="planned" if order_data["order_number"].startswith("PL") else "production",
                product_id=order_data["product_id"],
                quantity=order_data["quantity"],
                due_date=order_data["due_date"],
                priority=order_data["priority"],
                status="pending_schedule" if order_data["order_number"].startswith("PL") else "scheduled",
                description=order_data["description"]
            )

            if "confirmed_start" in order_data:
                order.confirmed_start = order_data["confirmed_start"]
                order.confirmed_end = order_data["confirmed_end"]

            db.add(order)
            db.commit()

            # Get routing for this product
            routing = db.query(models.Routing).filter(models.Routing.product_id == order.product_id).first()
            if routing:
                # Get operations for this routing
                operations = db.query(models.RoutingOperation).filter(models.RoutingOperation.routing_id == routing.id).order_by(models.RoutingOperation.sequence).all()

                # Create order operations
                for op in operations:
                    # Calculate run time
                    run_time = op.setup_time + (op.run_time_per_unit * order.quantity)
                    
                    order_operation = models.Operation(
                        order_id=order.id,
                        routing_operation_id=op.id,
                        sequence=op.sequence,
                        name=op.name,
                        setup_time=op.setup_time,
                        run_time=run_time,
                        scheduled_start=None,
                        scheduled_end=None,
                        status="pending" if order.order_type == "planned" else "scheduled"
                    )
                    db.add(order_operation)
                db.commit()

                # Production orders need resource allocation and scheduling times
                if order.order_type == "production" and operations:
                    # Calculate time allocation for each operation
                    total_time = (order.confirmed_end - order.confirmed_start).total_seconds() / 3600  # hours
                    operation_count = len(operations)
                    time_per_operation = total_time / operation_count if operation_count > 0 else 0

                    current_time = order.confirmed_start

                    for i, op in enumerate(operations):
                        op_start = current_time
                        op_end = op_start + timedelta(hours=time_per_operation)

                        # Update order operation
                        order_operation = db.query(models.Operation).filter(
                            models.Operation.order_id == order.id,
                            models.Operation.routing_operation_id == op.id
                        ).first()

                        if order_operation:
                            # Allocate resources for production orders
                            work_center_resources = [r for r in resources if r.work_center_id == op.work_center_id]
                            if work_center_resources:
                                # Get resource list for this work center and randomly select one
                                selected_resource = random.choice(work_center_resources)
                                order_operation.resource_id = selected_resource.id

                                # Calculate scheduling time - ensure each operation has time allocation
                                order_operation.scheduled_start = op_start
                                order_operation.scheduled_end = op_end
                                order_operation.status = "scheduled"

                        current_time = op_end

            orders.append(order)

        db.commit()

        planned_count = len([o for o in orders if o.order_type == "planned"])
        production_count = len([o for o in orders if o.order_type == "production"])

        print(f"Created {planned_count} planned orders")
        print(f"Created {production_count} production orders")

        # ==================== Setup Matrix ====================
        # Create setup groups
        setup_groups = [
            models.SetupGroup(code="SG-METAL", name="Metal Parts Group", description="Metal material products, tool change required for setup"),
            models.SetupGroup(code="SG-PLASTIC", name="Plastic Parts Group", description="Plastic material products"),
            models.SetupGroup(code="SG-LARGE", name="Large Parts Group", description="Large products, fixture adjustment required"),
            models.SetupGroup(code="SG-SMALL", name="Small Parts Group", description="Small products, precision machining"),
            models.SetupGroup(code="SG-STANDARD", name="Standard Parts Group", description="Standard specification products"),
        ]

        for sg in setup_groups:
            db.add(sg)
        db.commit()

        print(f"Created {len(setup_groups)} setup groups")

        # Assign products to setup groups
        # Get all products
        all_products = db.query(models.Product).all()

        product_assignments = []
        for product in all_products:
            # Assign setup groups based on product characteristics
            if "metal" in product.name.lower() or "steel" in product.name.lower() or "aluminum" in product.name.lower():
                group_id = setup_groups[0].id  # Metal parts group
            elif "plastic" in product.name.lower() or "resin" in product.name.lower():
                group_id = setup_groups[1].id  # Plastic parts group
            elif "housing" in product.name.lower() or "enclosure" in product.name.lower():
                group_id = setup_groups[2].id  # Large parts group
            elif "precision" in product.name.lower() or "sensor" in product.name.lower() or "connector" in product.name.lower():
                group_id = setup_groups[3].id  # Small parts group
            else:
                group_id = setup_groups[4].id  # Standard parts group

            assignment = models.ProductSetupGroup(
                product_id=product.id,
                setup_group_id=group_id,
                work_center_id=None  # Global assignment
            )
            product_assignments.append(assignment)
            db.add(assignment)

        db.commit()
        print(f"Created {len(product_assignments)} product-setup group assignments")

        # Create global setup matrix
        # Setup times between different setup groups (hours)
        matrix_data = [
            # From metal parts group to other groups
            (setup_groups[0].id, setup_groups[1].id, 1.5, "Metal→Plastic: Cleaning and tool change required"),
            (setup_groups[0].id, setup_groups[2].id, 0.5, "Metal→Large parts: Fixture adjustment"),
            (setup_groups[0].id, setup_groups[3].id, 1.0, "Metal→Small parts: Fixture and tool change"),
            (setup_groups[0].id, setup_groups[4].id, 0.3, "Metal→Standard parts: Simple adjustment"),
            # From plastic parts group to other groups
            (setup_groups[1].id, setup_groups[0].id, 2.0, "Plastic→Metal: Thorough cleaning and tool change"),
            (setup_groups[1].id, setup_groups[2].id, 1.0, "Plastic→Large parts: Equipment adjustment"),
            (setup_groups[1].id, setup_groups[3].id, 0.5, "Plastic→Small parts: Simple adjustment"),
            (setup_groups[1].id, setup_groups[4].id, 0.8, "Plastic→Standard parts: Cleaning and adjustment"),
            # From large parts group to other groups
            (setup_groups[2].id, setup_groups[0].id, 0.5, "Large parts→Metal: Fixture adjustment"),
            (setup_groups[2].id, setup_groups[1].id, 1.0, "Large parts→Plastic: Adjustment and cleaning"),
            (setup_groups[2].id, setup_groups[3].id, 1.5, "Large parts→Small parts: Fixture change"),
            (setup_groups[2].id, setup_groups[4].id, 0.3, "Large parts→Standard parts: Simple adjustment"),
            # From small parts group to other groups
            (setup_groups[3].id, setup_groups[0].id, 1.0, "Small parts→Metal: Tool and fixture change"),
            (setup_groups[3].id, setup_groups[1].id, 0.5, "Small parts→Plastic: Simple adjustment"),
            (setup_groups[3].id, setup_groups[2].id, 1.5, "Small parts→Large parts: Fixture change"),
            (setup_groups[3].id, setup_groups[4].id, 0.2, "Small parts→Standard parts: Fine tuning"),
            # From standard parts group to other groups
            (setup_groups[4].id, setup_groups[0].id, 0.3, "Standard parts→Metal: Simple adjustment"),
            (setup_groups[4].id, setup_groups[1].id, 0.8, "Standard parts→Plastic: Cleaning and adjustment"),
            (setup_groups[4].id, setup_groups[2].id, 0.3, "Standard parts→Large parts: Simple adjustment"),
            (setup_groups[4].id, setup_groups[3].id, 0.2, "Standard parts→Small parts: Fine tuning"),
        ]

        for from_group_id, to_group_id, setup_time, description in matrix_data:
            matrix_record = models.SetupMatrix(
                from_setup_group_id=from_group_id,
                to_setup_group_id=to_group_id,
                changeover_time=setup_time,
                description=description,
                work_center_id=None  # Global matrix
            )
            db.add(matrix_record)

        db.commit()
        print(f"Created {len(matrix_data)} setup matrix records")

        print("Demo data creation completed!")
        print("Data summary:")
        print(f"  - Work centers: {db.query(models.WorkCenter).count()}")
        print(f"  - Resources: {db.query(models.Resource).count()}")
        print(f"  - Products (materials): {db.query(models.Product).count()}")
        print(f"  - Routings: {db.query(models.Routing).count()}")
        print(f"  - Planned orders: {planned_count}")
        print(f"  - Production orders: {production_count}")
        print(f"  - Operations: {db.query(models.Operation).count()}")
        print(f"  - Setup groups: {db.query(models.SetupGroup).count()}")
        print(f"  - Setup matrix: {db.query(models.SetupMatrix).count()}")

    except Exception as e:
        print(f"Failed to create demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Initialize APS demo data (English version)')
    parser.add_argument('--force', action='store_true', help='Force recreation of data (clear existing data)')

    args = parser.parse_args()

    try:
        create_demo_data(force=args.force)
        print("\nDemo data initialization completed successfully!")
    except Exception as e:
        print(f"\nDemo data initialization failed: {e}")
        sys.exit(1)