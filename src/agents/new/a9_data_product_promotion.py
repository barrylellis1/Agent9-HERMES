"""
Data Product Promotion Module

Handles promotion of data product contracts from staging to production
after governance approval.
"""

import os
import shutil
import yaml
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataProductPromoter:
    """Promotes data product contracts from staging to production"""
    
    def __init__(self):
        self.staging_dir = "src/registry_references/data_product_registry/staging"
        self.production_dir = "src/registry_references/data_product_registry/data_products"
        self.registry_file = "src/registry_references/data_product_registry/data_product_registry.yaml"
        self.archive_dir = "src/registry_references/data_product_registry/staging/archive"
    
    def promote_to_production(
        self,
        data_product_id: str,
        approved_by: str,
        approval_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Promote a data product contract from staging to production.
        
        Args:
            data_product_id: ID of the data product to promote
            approved_by: Principal ID of the approver
            approval_notes: Optional notes about the approval
            
        Returns:
            Dict with status, message, and paths
        """
        try:
            staging_path = os.path.join(self.staging_dir, f"{data_product_id}.yaml")
            production_path = os.path.join(self.production_dir, f"{data_product_id}.yaml")
            
            # Validate staging contract exists
            if not os.path.exists(staging_path):
                return {
                    "success": False,
                    "error": f"Staging contract not found: {staging_path}"
                }
            
            # Load and validate staging contract
            with open(staging_path, 'r', encoding='utf-8') as f:
                contract = yaml.safe_load(f)
            
            validation_result = self._validate_for_promotion(contract)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Contract failed promotion validation",
                    "validation_errors": validation_result["errors"]
                }
            
            # Add promotion metadata
            if "metadata" not in contract:
                contract["metadata"] = {}
            
            contract["metadata"]["promoted_at"] = datetime.utcnow().isoformat()
            contract["metadata"]["approved_by"] = approved_by
            if approval_notes:
                contract["metadata"]["approval_notes"] = approval_notes
            contract["metadata"]["status"] = "production"
            
            # Ensure production directory exists
            os.makedirs(self.production_dir, exist_ok=True)
            
            # Write to production
            with open(production_path, 'w', encoding='utf-8') as f:
                yaml.dump(contract, f, sort_keys=False, allow_unicode=True)
            
            logger.info(f"Promoted {data_product_id} to production: {production_path}")
            
            # Update registry
            registry_updated = self._update_registry(contract, production_path)
            
            # Archive staging copy
            self._archive_staging_contract(staging_path, data_product_id)
            
            return {
                "success": True,
                "message": f"Data product {data_product_id} promoted to production",
                "production_path": production_path,
                "registry_updated": registry_updated
            }
            
        except Exception as e:
            logger.error(f"Error promoting data product: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_for_promotion(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a contract meets all requirements for promotion.
        
        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []
        
        # Check metadata
        metadata = contract.get("metadata", {})
        if not metadata.get("id"):
            errors.append("Missing metadata.id")
        if not metadata.get("name"):
            errors.append("Missing metadata.name")
        if not metadata.get("domain"):
            errors.append("Missing metadata.domain")
        
        # Check KPIs
        kpis = contract.get("kpis", [])
        if not kpis:
            errors.append("No KPIs defined")
        else:
            for i, kpi in enumerate(kpis):
                if not kpi.get("id"):
                    errors.append(f"KPI {i}: Missing id")
                if not kpi.get("name"):
                    errors.append(f"KPI {i}: Missing name")
                if not kpi.get("sql_query"):
                    errors.append(f"KPI {i}: Missing sql_query")
                
                # Check strategic metadata
                kpi_metadata = kpi.get("metadata", {})
                if not kpi_metadata.get("line"):
                    errors.append(f"KPI {i} ({kpi.get('id')}): Missing strategic metadata 'line'")
                if not kpi_metadata.get("altitude"):
                    errors.append(f"KPI {i} ({kpi.get('id')}): Missing strategic metadata 'altitude'")
                if not kpi_metadata.get("profit_driver_type"):
                    errors.append(f"KPI {i} ({kpi.get('id')}): Missing strategic metadata 'profit_driver_type'")
        
        # Check governance metadata
        governance = contract.get("governance", {})
        if not governance.get("owner_role"):
            errors.append("Missing governance.owner_role")
        if not governance.get("stakeholder_roles"):
            errors.append("Missing governance.stakeholder_roles")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _update_registry(self, contract: Dict[str, Any], production_path: str) -> bool:
        """
        Add the promoted data product to the registry.
        
        Returns:
            True if registry was updated successfully
        """
        try:
            # Load existing registry
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    registry = yaml.safe_load(f) or {}
            else:
                registry = {"data_products": []}
            
            if "data_products" not in registry:
                registry["data_products"] = []
            
            metadata = contract.get("metadata", {})
            
            # Check if already exists
            existing_index = None
            for i, dp in enumerate(registry["data_products"]):
                if dp.get("product_id") == metadata.get("id"):
                    existing_index = i
                    break
            
            # Create registry entry
            entry = {
                "product_id": metadata.get("id"),
                "name": metadata.get("name"),
                "domain": metadata.get("domain"),
                "description": metadata.get("description", ""),
                "source_system": metadata.get("source_system", "unknown"),
                "tags": metadata.get("tags", []),
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                "reviewed": True,
                "yaml_contract_path": production_path,
                "promoted_at": metadata.get("promoted_at"),
                "approved_by": metadata.get("approved_by")
            }
            
            # Update or append
            if existing_index is not None:
                registry["data_products"][existing_index] = entry
                logger.info(f"Updated existing registry entry for {metadata.get('id')}")
            else:
                registry["data_products"].append(entry)
                logger.info(f"Added new registry entry for {metadata.get('id')}")
            
            # Write back to registry
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                yaml.dump(registry, f, sort_keys=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating registry: {e}")
            return False
    
    def _archive_staging_contract(self, staging_path: str, data_product_id: str):
        """Archive the staging contract after promotion"""
        try:
            os.makedirs(self.archive_dir, exist_ok=True)
            archive_path = os.path.join(
                self.archive_dir,
                f"{data_product_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yaml"
            )
            shutil.copy2(staging_path, archive_path)
            os.remove(staging_path)
            logger.info(f"Archived staging contract to {archive_path}")
        except Exception as e:
            logger.warning(f"Failed to archive staging contract: {e}")
    
    def reject_contract(
        self,
        data_product_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a data product contract and move to archive.
        
        Args:
            data_product_id: ID of the data product to reject
            rejected_by: Principal ID of the rejector
            rejection_reason: Reason for rejection
            
        Returns:
            Dict with status and message
        """
        try:
            staging_path = os.path.join(self.staging_dir, f"{data_product_id}.yaml")
            
            if not os.path.exists(staging_path):
                return {
                    "success": False,
                    "error": f"Staging contract not found: {staging_path}"
                }
            
            # Load contract and add rejection metadata
            with open(staging_path, 'r', encoding='utf-8') as f:
                contract = yaml.safe_load(f)
            
            if "metadata" not in contract:
                contract["metadata"] = {}
            
            contract["metadata"]["status"] = "rejected"
            contract["metadata"]["rejected_at"] = datetime.utcnow().isoformat()
            contract["metadata"]["rejected_by"] = rejected_by
            contract["metadata"]["rejection_reason"] = rejection_reason
            
            # Save to archive
            os.makedirs(self.archive_dir, exist_ok=True)
            archive_path = os.path.join(
                self.archive_dir,
                f"{data_product_id}_rejected_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.yaml"
            )
            
            with open(archive_path, 'w', encoding='utf-8') as f:
                yaml.dump(contract, f, sort_keys=False, allow_unicode=True)
            
            # Remove from staging
            os.remove(staging_path)
            
            logger.info(f"Rejected and archived {data_product_id}: {archive_path}")
            
            return {
                "success": True,
                "message": f"Data product {data_product_id} rejected and archived",
                "archive_path": archive_path
            }
            
        except Exception as e:
            logger.error(f"Error rejecting data product: {e}")
            return {
                "success": False,
                "error": str(e)
            }
