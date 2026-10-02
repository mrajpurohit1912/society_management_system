'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { useAuthStore } from '@/lib/store/auth-store';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Building2,
  Home,
  Layers,
  PlusCircle,
  Loader2,
  AlertCircle,
  CheckCircle,
  Sparkles,
  ChevronRight,
  DoorOpen,
  Sliders,
  Plus,
  Trash2,
  Pencil,
  X,
} from 'lucide-react';

interface Building {
  id: string;
  society_id: string;
  name: string;
  created_at: string;
}

interface Floor {
  id: string;
  building_id: string;
  floor_number: number;
  floor_name?: string;
}

interface Unit {
  id: string;
  floor_id: string;
  unit_number: string;
  unit_type: string;
  status: string;
}

interface FloorOverride {
  floor_number: number;
  floor_name: string;
  units_count: number;
  unit_prefix: string;
}

export default function AdminUnitsPage() {
  const user = useAuthStore((state) => state.user);
  const societyId = user?.active_society_id;

  const [buildings, setBuildings] = useState<Building[]>([]);
  const [selectedBuilding, setSelectedBuilding] = useState<Building | null>(null);
  const [floors, setFloors] = useState<Floor[]>([]);
  const [unitsByFloor, setUnitsByFloor] = useState<Record<string, Unit[]>>({});
  
  const [loading, setLoading] = useState(true);
  const [floorsLoading, setFloorsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Bulk Provision State
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkTowerName, setBulkTowerName] = useState('Tower A');
  const [bulkNumFloors, setBulkNumFloors] = useState(5);
  const [bulkUnitsPerFloor, setBulkUnitsPerFloor] = useState(4);
  const [showFloorCustomizer, setShowFloorCustomizer] = useState(false);
  const [customFloorList, setCustomFloorList] = useState<FloorOverride[]>([]);

  // Single Building State (Add / Edit)
  const [showAddBuilding, setShowAddBuilding] = useState(false);
  const [newBuildingName, setNewBuildingName] = useState('');
  const [showEditBuildingModal, setShowEditBuildingModal] = useState(false);
  const [editBuildingName, setEditBuildingName] = useState('');

  // Add Floor State (to selected building)
  const [showAddFloorModal, setShowAddFloorModal] = useState(false);
  const [newFloorNumber, setNewFloorNumber] = useState(1);
  const [newFloorName, setNewFloorName] = useState('Floor 1');
  const [newFloorUnitsCount, setNewFloorUnitsCount] = useState(4);

  // Edit Floor State
  const [editingFloor, setEditingFloor] = useState<Floor | null>(null);
  const [editFloorName, setEditFloorName] = useState('');

  // Add Unit State (to specific floor)
  const [targetFloorForUnit, setTargetFloorForUnit] = useState<Floor | null>(null);
  const [newUnitNumber, setNewUnitNumber] = useState('');
  const [newUnitType, setNewUnitType] = useState('flat');
  const [newUnitStatus, setNewUnitStatus] = useState('vacant');

  // Edit Unit State
  const [editingUnit, setEditingUnit] = useState<{ unit: Unit; floorId: string } | null>(null);
  const [editUnitNumber, setEditUnitNumber] = useState('');
  const [editUnitType, setEditUnitType] = useState('flat');
  const [editUnitStatus, setEditUnitStatus] = useState('vacant');

  // Quick Populate Existing Wing State (1 API call)
  const [showQuickPopulateModal, setShowQuickPopulateModal] = useState(false);
  const [quickFloors, setQuickFloors] = useState(5);
  const [quickUnitsPerFloor, setQuickUnitsPerFloor] = useState(4);

  // Synchronize Floor Customizer list whenever total floors or default units changes
  useEffect(() => {
    const list: FloorOverride[] = [];
    for (let f = 0; f <= bulkNumFloors; f++) {
      const defaultName = f === 0 ? 'Ground Floor' : `Floor ${f}`;
      const defaultPrefix = f === 0 ? 'G' : '';
      list.push({
        floor_number: f,
        floor_name: defaultName,
        units_count: bulkUnitsPerFloor,
        unit_prefix: defaultPrefix,
      });
    }
    setCustomFloorList(list);
  }, [bulkNumFloors, bulkUnitsPerFloor]);

  // Fetch Buildings
  const fetchBuildings = useCallback(async () => {
    if (!societyId) {
      setLoading(false);
      return;
    }
    try {
      const res = await apiClient.get(`/societies/${societyId}/buildings`);
      const list = res.data?.data || res.data || [];
      const buildingArray = Array.isArray(list) ? list : [];
      setBuildings(buildingArray);
      if (buildingArray.length > 0 && !selectedBuilding) {
        setSelectedBuilding(buildingArray[0]);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setLoading(false);
    }
  }, [societyId, selectedBuilding]);

  useEffect(() => {
    fetchBuildings();
  }, [fetchBuildings]);

  // Fetch Floors & Units for Selected Building
  const refreshFloorsAndUnits = useCallback(async () => {
    if (!societyId || !selectedBuilding) return;

    setFloorsLoading(true);
    try {
      const floorRes = await apiClient.get(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors`
      );
      const floorList: Floor[] = floorRes.data?.data || floorRes.data || [];
      setFloors(Array.isArray(floorList) ? floorList : []);

      const unitPromises = floorList.map(async (floor) => {
        try {
          const uRes = await apiClient.get(
            `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${floor.id}/units`
          );
          const uList = uRes.data?.data || uRes.data || [];
          return { floorId: floor.id, units: Array.isArray(uList) ? uList : [] };
        } catch {
          return { floorId: floor.id, units: [] };
        }
      });

      const results = await Promise.all(unitPromises);
      const mapping: Record<string, Unit[]> = {};
      for (const item of results) {
        mapping[item.floorId] = item.units;
      }
      setUnitsByFloor(mapping);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      }
    } finally {
      setFloorsLoading(false);
    }
  }, [societyId, selectedBuilding]);

  useEffect(() => {
    refreshFloorsAndUnits();
  }, [refreshFloorsAndUnits]);

  // Bulk Provision Action (With Duplicate Check & Custom Floors)
  const handleBulkProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    const cleanName = bulkTowerName.trim();
    if (buildings.some((b) => b.name.trim().toLowerCase() === cleanName.toLowerCase())) {
      setFeedback({
        type: 'error',
        message: `A building or wing named "${cleanName}" already exists in this society. Please choose a different name.`,
      });
      return;
    }

    setActionLoading(true);
    setFeedback(null);

    try {
      const payload: any = {
        name: cleanName,
        number_of_floors: Number(bulkNumFloors),
        units_per_floor: Number(bulkUnitsPerFloor),
      };

      if (showFloorCustomizer && customFloorList.length > 0) {
        payload.custom_floors = customFloorList.map((cf) => ({
          floor_number: cf.floor_number,
          floor_name: cf.floor_name.trim(),
          units_count: Number(cf.units_count),
          unit_prefix: cf.unit_prefix.trim() || undefined,
        }));
      }

      await apiClient.post(`/societies/${societyId}/provision`, {
        buildings: [payload],
      });

      setFeedback({
        type: 'success',
        message: `Successfully provisioned ${cleanName} with customized floors and flats!`,
      });
      setShowBulkModal(false);
      setShowFloorCustomizer(false);
      await fetchBuildings();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to provision tower structure.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Create Single Building (With Duplicate Check)
  const handleCreateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !newBuildingName.trim()) return;

    const cleanName = newBuildingName.trim();

    if (buildings.some((b) => b.name.trim().toLowerCase() === cleanName.toLowerCase())) {
      setFeedback({
        type: 'error',
        message: `A building or wing named "${cleanName}" already exists in this society. Please choose a unique name.`,
      });
      return;
    }

    setActionLoading(true);
    setFeedback(null);

    try {
      const res = await apiClient.post(`/societies/${societyId}/buildings`, {
        name: cleanName,
      });
      const created = res.data?.data || res.data;
      setFeedback({ type: 'success', message: `Building "${created.name}" created successfully!` });
      setNewBuildingName('');
      setShowAddBuilding(false);
      await fetchBuildings();
      setSelectedBuilding(created);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to create building.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Update Building Name
  const handleUpdateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding || !editBuildingName.trim()) return;

    const cleanName = editBuildingName.trim();
    if (
      buildings.some(
        (b) => b.id !== selectedBuilding.id && b.name.trim().toLowerCase() === cleanName.toLowerCase()
      )
    ) {
      setFeedback({
        type: 'error',
        message: `A building or wing named "${cleanName}" already exists.`,
      });
      return;
    }

    setActionLoading(true);
    setFeedback(null);

    try {
      const res = await apiClient.patch(`/societies/${societyId}/buildings/${selectedBuilding.id}`, {
        name: cleanName,
      });
      const updated = res.data?.data || res.data;
      setFeedback({ type: 'success', message: `Building renamed to "${updated.name}" successfully!` });
      setShowEditBuildingModal(false);
      setSelectedBuilding(updated);
      await fetchBuildings();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to rename building.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Building / Wing
  const handleDeleteBuilding = async () => {
    if (!societyId || !selectedBuilding) return;
    if (
      !confirm(
        `Are you sure you want to delete "${selectedBuilding.name}"? All its floors and flats will be permanently removed.`
      )
    ) {
      return;
    }

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.delete(`/societies/${societyId}/buildings/${selectedBuilding.id}`);
      setFeedback({ type: 'success', message: `Building "${selectedBuilding.name}" deleted successfully!` });
      const remaining = buildings.filter((b) => b.id !== selectedBuilding.id);
      setBuildings(remaining);
      setSelectedBuilding(remaining.length > 0 ? remaining[0] : null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to delete building.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Add Floor to Existing Building
  const handleCreateFloor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      const floorRes = await apiClient.post(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors`,
        {
          floor_number: Number(newFloorNumber),
          floor_name: newFloorName.trim() || `Floor ${newFloorNumber}`,
        }
      );
      const createdFloor = floorRes.data?.data || floorRes.data;

      // Auto-generate units for this new floor if specified
      if (newFloorUnitsCount > 0 && createdFloor?.id) {
        for (let idx = 1; idx <= newFloorUnitsCount; idx++) {
          const unitNumber = `${newFloorNumber}${String(idx).padStart(2, '0')}`;
          await apiClient.post(
            `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${createdFloor.id}/units`,
            {
              unit_number: unitNumber,
              unit_type: 'flat',
              status: 'vacant',
            }
          );
        }
      }

      setFeedback({
        type: 'success',
        message: `Floor ${newFloorNumber} (${newFloorName}) with ${newFloorUnitsCount} flats created successfully!`,
      });
      setShowAddFloorModal(false);
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to create floor.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Update Floor Name
  const handleUpdateFloor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding || !editingFloor) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.patch(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${editingFloor.id}`,
        {
          floor_name: editFloorName.trim(),
        }
      );

      setFeedback({ type: 'success', message: 'Floor updated successfully!' });
      setEditingFloor(null);
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to update floor.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Floor
  const handleDeleteFloor = async (floorId: string, floorName: string) => {
    if (!societyId || !selectedBuilding) return;
    if (!confirm(`Are you sure you want to delete ${floorName}? All flats on this floor will also be deleted.`)) {
      return;
    }

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.delete(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${floorId}`
      );
      setFeedback({ type: 'success', message: `${floorName} deleted successfully!` });
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to delete floor.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Add Single Flat / Unit to Floor
  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding || !targetFloorForUnit || !newUnitNumber.trim()) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.post(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${targetFloorForUnit.id}/units`,
        {
          unit_number: newUnitNumber.trim(),
          unit_type: newUnitType,
          status: newUnitStatus,
        }
      );

      setFeedback({
        type: 'success',
        message: `Flat ${newUnitNumber.trim()} added successfully to ${targetFloorForUnit.floor_name || `Floor ${targetFloorForUnit.floor_number}`}!`,
      });
      setTargetFloorForUnit(null);
      setNewUnitNumber('');
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to add flat.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Update Flat / Unit
  const handleUpdateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding || !editingUnit || !editUnitNumber.trim()) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.patch(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${editingUnit.floorId}/units/${editingUnit.unit.id}`,
        {
          unit_number: editUnitNumber.trim(),
          unit_type: editUnitType,
          status: editUnitStatus,
        }
      );

      setFeedback({ type: 'success', message: `Flat ${editUnitNumber.trim()} updated successfully!` });
      setEditingUnit(null);
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to update flat.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Flat / Unit
  const handleDeleteUnit = async () => {
    if (!societyId || !selectedBuilding || !editingUnit) return;
    if (!confirm(`Are you sure you want to delete Flat ${editingUnit.unit.unit_number}?`)) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.delete(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/floors/${editingUnit.floorId}/units/${editingUnit.unit.id}`
      );
      setFeedback({ type: 'success', message: `Flat ${editingUnit.unit.unit_number} deleted successfully!` });
      setEditingUnit(null);
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to delete flat.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  // Quick Populate Empty Wing in 1 Single API Call!
  const handleQuickPopulateWing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !selectedBuilding) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      // 1 single atomic bulk API call (no loop of 450 requests!)
      await apiClient.post(
        `/societies/${societyId}/buildings/${selectedBuilding.id}/populate`,
        {
          number_of_floors: Number(quickFloors),
          units_per_floor: Number(quickUnitsPerFloor),
        }
      );

      setFeedback({
        type: 'success',
        message: `Successfully populated ${selectedBuilding.name} with ${Number(quickFloors) + 1} floors and ${(Number(quickFloors) + 1) * Number(quickUnitsPerFloor)} flats in 1 request!`,
      });
      setShowQuickPopulateModal(false);
      await refreshFloorsAndUnits();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFeedback({ type: 'error', message: err.message });
      } else {
        setFeedback({ type: 'error', message: 'Failed to populate wing.' });
      }
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 flex items-center gap-2">
            <Home className="h-6 w-6" />
            <span>Towers, Floors & Units Directory</span>
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Manage your society&apos;s physical architectural inventory, towers, floors, and flat units.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {selectedBuilding && (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setNewFloorNumber(floors.length);
                  setNewFloorName(`Floor ${floors.length}`);
                  setShowAddFloorModal(true);
                }}
                className="flex items-center gap-1.5 h-8 text-xs font-medium"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add Floor</span>
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setEditBuildingName(selectedBuilding.name);
                  setShowEditBuildingModal(true);
                }}
                className="flex items-center gap-1.5 h-8 text-xs"
                title="Rename Wing"
              >
                <Pencil className="h-3.5 w-3.5 text-zinc-500" />
                <span className="hidden sm:inline">Rename Wing</span>
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={handleDeleteBuilding}
                className="flex items-center gap-1.5 h-8 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                title="Delete Wing"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Delete Wing</span>
              </Button>
            </>
          )}

          <Button
            size="sm"
            onClick={() => setShowBulkModal(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1.5 h-8 text-xs font-semibold"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>1-Click Bulk Generator</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddBuilding(!showAddBuilding)}
            className="flex items-center gap-1.5 h-8 text-xs"
          >
            <PlusCircle className="h-3.5 w-3.5" />
            <span>Add Building</span>
          </Button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-3.5 rounded-lg text-sm flex items-center gap-2 border ${
            feedback.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/50 dark:border-emerald-900 dark:text-emerald-300'
              : 'bg-red-50 border-red-200 text-red-800 dark:bg-red-950/50 dark:border-red-900 dark:text-red-300'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Edit Building Name Modal */}
      {showEditBuildingModal && selectedBuilding && (
        <Card className="border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Pencil className="h-4 w-4 text-indigo-600" />
              <span>Rename Wing &quot;{selectedBuilding.name}&quot;</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdateBuilding} className="flex gap-2">
              <Input
                value={editBuildingName}
                onChange={(e) => setEditBuildingName(e.target.value)}
                placeholder="New Wing Name (e.g. Tower C)"
                required
                className="h-9 text-sm max-w-sm bg-white dark:bg-zinc-950"
              />
              <Button type="submit" size="sm" disabled={actionLoading} className="h-9 text-xs">
                {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowEditBuildingModal(false)}
                className="h-9 text-xs"
              >
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Bulk Provisioning Modal Drawer */}
      {showBulkModal && (
        <Card className="border-2 border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-indigo-950 dark:text-indigo-200 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <span>Bulk Society Structure Provisioning</span>
            </CardTitle>
            <CardDescription className="text-xs text-zinc-600 dark:text-zinc-400">
              Instantly generate an entire building tower with customizable floors and flat unit counts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBulkProvision} className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="space-y-1 sm:col-span-2">
                <Label htmlFor="bulkTower" className="text-xs font-medium">
                  Tower / Building Name
                </Label>
                <Input
                  id="bulkTower"
                  value={bulkTowerName}
                  onChange={(e) => setBulkTowerName(e.target.value)}
                  placeholder="e.g. Tower A or Wing B"
                  required
                  className="h-9 text-sm bg-white dark:bg-zinc-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="bulkFloors" className="text-xs font-medium">
                  Total Floors (1-100)
                </Label>
                <Input
                  id="bulkFloors"
                  type="number"
                  min={1}
                  max={100}
                  value={bulkNumFloors}
                  onChange={(e) => setBulkNumFloors(parseInt(e.target.value) || 1)}
                  required
                  className="h-9 text-sm bg-white dark:bg-zinc-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="bulkUnits" className="text-xs font-medium">
                  Default Units / Floor
                </Label>
                <Input
                  id="bulkUnits"
                  type="number"
                  min={1}
                  max={20}
                  value={bulkUnitsPerFloor}
                  onChange={(e) => setBulkUnitsPerFloor(parseInt(e.target.value) || 1)}
                  required
                  className="h-9 text-sm bg-white dark:bg-zinc-900"
                />
              </div>

              {/* Expandable Custom Floors Section */}
              <div className="sm:col-span-4 border-t border-indigo-200 dark:border-indigo-800 pt-3">
                <button
                  type="button"
                  onClick={() => setShowFloorCustomizer(!showFloorCustomizer)}
                  className="text-xs font-semibold text-indigo-700 dark:text-indigo-400 flex items-center gap-1.5 hover:underline"
                >
                  <Sliders className="h-3.5 w-3.5" />
                  <span>
                    {showFloorCustomizer ? 'Hide custom floor overrides' : 'Customize individual floor counts (Ground, Penthouse, etc.)'}
                  </span>
                </button>

                {showFloorCustomizer && (
                  <div className="mt-3 p-3 bg-white dark:bg-zinc-900 rounded-lg border border-indigo-100 dark:border-indigo-900/50 space-y-2 max-h-60 overflow-y-auto">
                    <p className="text-[11px] text-zinc-500 mb-2">
                      Adjust unit counts or names for specific floors (e.g. fewer units on Ground or Penthouse floors).
                    </p>
                    <div className="grid grid-cols-12 gap-2 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400 px-1">
                      <span className="col-span-2">Floor #</span>
                      <span className="col-span-4">Floor Name</span>
                      <span className="col-span-3">Units Count</span>
                      <span className="col-span-3">Unit Prefix</span>
                    </div>

                    {customFloorList.map((cf, idx) => (
                      <div key={cf.floor_number} className="grid grid-cols-12 gap-2 items-center">
                        <span className="col-span-2 text-xs font-bold text-zinc-700 dark:text-zinc-300">
                          {cf.floor_number === 0 ? 'G (0)' : `F-${cf.floor_number}`}
                        </span>
                        <Input
                          value={cf.floor_name}
                          onChange={(e) => {
                            const updated = [...customFloorList];
                            updated[idx].floor_name = e.target.value;
                            setCustomFloorList(updated);
                          }}
                          className="col-span-4 h-7 text-xs"
                          placeholder="e.g. Ground"
                        />
                        <Input
                          type="number"
                          min={0}
                          max={50}
                          value={cf.units_count}
                          onChange={(e) => {
                            const updated = [...customFloorList];
                            updated[idx].units_count = parseInt(e.target.value) || 0;
                            setCustomFloorList(updated);
                          }}
                          className="col-span-3 h-7 text-xs"
                        />
                        <Input
                          value={cf.unit_prefix}
                          onChange={(e) => {
                            const updated = [...customFloorList];
                            updated[idx].unit_prefix = e.target.value;
                            setCustomFloorList(updated);
                          }}
                          placeholder="e.g. G or PH"
                          className="col-span-3 h-7 text-xs"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="sm:col-span-4 flex items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowBulkModal(false)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={actionLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white h-8 text-xs flex items-center gap-1.5"
                >
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                  <span>
                    Generate{' '}
                    {showFloorCustomizer
                      ? customFloorList.reduce((acc, curr) => acc + (Number(curr.units_count) || 0), 0)
                      : (bulkNumFloors + 1) * bulkUnitsPerFloor}{' '}
                    Flats Now
                  </span>
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Add Single Building Form */}
      {showAddBuilding && (
        <Card className="border border-zinc-200 dark:border-zinc-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Add New Building / Tower</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateBuilding} className="flex gap-2">
              <Input
                value={newBuildingName}
                onChange={(e) => setNewBuildingName(e.target.value)}
                placeholder="Building Name (e.g. Block C)"
                required
                className="h-9 text-sm max-w-sm"
              />
              <Button type="submit" size="sm" disabled={actionLoading} className="h-9 text-xs">
                {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Create'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowAddBuilding(false)}
                className="h-9 text-xs"
              >
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Add Floor to Selected Building Modal */}
      {showAddFloorModal && selectedBuilding && (
        <Card className="border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-600" />
              <span>Add New Floor to {selectedBuilding.name}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateFloor} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Floor Number</Label>
                <Input
                  type="number"
                  min={0}
                  max={150}
                  value={newFloorNumber}
                  onChange={(e) => {
                    const num = parseInt(e.target.value) || 0;
                    setNewFloorNumber(num);
                    setNewFloorName(num === 0 ? 'Ground Floor' : `Floor ${num}`);
                  }}
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Floor Name / Label</Label>
                <Input
                  value={newFloorName}
                  onChange={(e) => setNewFloorName(e.target.value)}
                  placeholder="e.g. Penthouse or Ground"
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Auto-Generate Flats</Label>
                <Input
                  type="number"
                  min={0}
                  max={30}
                  value={newFloorUnitsCount}
                  onChange={(e) => setNewFloorUnitsCount(parseInt(e.target.value) || 0)}
                  placeholder="e.g. 4"
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="sm:col-span-3 flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddFloorModal(false)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={actionLoading} className="h-8 text-xs">
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Create Floor'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Edit Floor Modal */}
      {editingFloor && selectedBuilding && (
        <Card className="border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Pencil className="h-4 w-4 text-indigo-600" />
              <span>Edit Floor {editingFloor.floor_number} Name</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdateFloor} className="flex gap-2">
              <Input
                value={editFloorName}
                onChange={(e) => setEditFloorName(e.target.value)}
                placeholder="Floor Name (e.g. Ground Floor, Penthouse)"
                required
                className="h-9 text-sm max-w-sm bg-white dark:bg-zinc-950"
              />
              <Button type="submit" size="sm" disabled={actionLoading} className="h-9 text-xs">
                {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save'}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setEditingFloor(null)}
                className="h-9 text-xs"
              >
                Cancel
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Add Single Flat Modal */}
      {targetFloorForUnit && selectedBuilding && (
        <Card className="border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <DoorOpen className="h-4 w-4 text-emerald-600" />
              <span>
                Add Flat to {targetFloorForUnit.floor_name || `Floor ${targetFloorForUnit.floor_number}`} ({selectedBuilding.name})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateUnit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Flat / Unit Number</Label>
                <Input
                  value={newUnitNumber}
                  onChange={(e) => setNewUnitNumber(e.target.value)}
                  placeholder="e.g. 101, 102A, PH-1"
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Unit Type</Label>
                <select
                  value={newUnitType}
                  onChange={(e) => setNewUnitType(e.target.value)}
                  className="w-full h-8 text-xs border rounded-md px-2 bg-white dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                >
                  <option value="flat">Flat / Apartment</option>
                  <option value="penthouse">Penthouse</option>
                  <option value="villa">Villa</option>
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Occupancy Status</Label>
                <select
                  value={newUnitStatus}
                  onChange={(e) => setNewUnitStatus(e.target.value)}
                  className="w-full h-8 text-xs border rounded-md px-2 bg-white dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                >
                  <option value="vacant">Vacant</option>
                  <option value="occupied">Occupied</option>
                  <option value="maintenance">Under Maintenance</option>
                </select>
              </div>

              <div className="sm:col-span-3 flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setTargetFloorForUnit(null)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={actionLoading} className="h-8 text-xs">
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save Flat'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Edit or Delete Flat Modal */}
      {editingUnit && selectedBuilding && (
        <Card className="border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900/60">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Pencil className="h-4 w-4 text-indigo-600" />
                <span>Edit Flat {editingUnit.unit.unit_number}</span>
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setEditingUnit(null)}
                className="h-6 w-6 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpdateUnit} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Flat / Unit Number</Label>
                <Input
                  value={editUnitNumber}
                  onChange={(e) => setEditUnitNumber(e.target.value)}
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Unit Type</Label>
                <select
                  value={editUnitType}
                  onChange={(e) => setEditUnitType(e.target.value)}
                  className="w-full h-8 text-xs border rounded-md px-2 bg-white dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                >
                  <option value="flat">Flat / Apartment</option>
                  <option value="penthouse">Penthouse</option>
                  <option value="villa">Villa</option>
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Occupancy Status</Label>
                <select
                  value={editUnitStatus}
                  onChange={(e) => setEditUnitStatus(e.target.value)}
                  className="w-full h-8 text-xs border rounded-md px-2 bg-white dark:bg-zinc-950 border-zinc-200 dark:border-zinc-800"
                >
                  <option value="vacant">Vacant</option>
                  <option value="occupied">Occupied</option>
                  <option value="maintenance">Under Maintenance</option>
                </select>
              </div>

              <div className="sm:col-span-3 flex justify-between items-center pt-2 border-t border-zinc-200 dark:border-zinc-800">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleDeleteUnit}
                  className="h-8 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950 flex items-center gap-1"
                >
                  <Trash2 className="h-3 w-3" />
                  <span>Delete Flat</span>
                </Button>

                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setEditingUnit(null)}
                    className="h-8 text-xs"
                  >
                    Cancel
                  </Button>
                  <Button type="submit" size="sm" disabled={actionLoading} className="h-8 text-xs">
                    {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Save Changes'}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Quick Populate Wing Modal (1 Single Fast API Call) */}
      {showQuickPopulateModal && selectedBuilding && (
        <Card className="border border-indigo-300 dark:border-indigo-800 bg-indigo-50/40 dark:bg-indigo-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              <span>Quick-Populate Floors & Flats for &quot;{selectedBuilding.name}&quot;</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Generate all floors and flats in 1 single instantaneous database transaction.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleQuickPopulateWing} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Total Floors (1-50)</Label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={quickFloors}
                  onChange={(e) => setQuickFloors(parseInt(e.target.value) || 1)}
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs">Units Per Floor (1-20)</Label>
                <Input
                  type="number"
                  min={1}
                  max={20}
                  value={quickUnitsPerFloor}
                  onChange={(e) => setQuickUnitsPerFloor(parseInt(e.target.value) || 1)}
                  required
                  className="h-8 text-xs bg-white dark:bg-zinc-950"
                />
              </div>

              <div className="sm:col-span-2 flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowQuickPopulateModal(false)}
                  className="h-8 text-xs"
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={actionLoading} className="h-8 text-xs bg-indigo-600 text-white">
                  {actionLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : `Generate ${(quickFloors + 1) * quickUnitsPerFloor} Flats (1 Call)`}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Buildings Navigation Tabs */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      ) : buildings.length === 0 ? (
        <Card className="border border-dashed border-zinc-300 dark:border-zinc-800 text-center py-16">
          <Building2 className="h-12 w-12 text-zinc-400 mx-auto mb-3" />
          <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
            No Buildings or Towers Configured Yet
          </h2>
          <p className="text-xs text-zinc-500 max-w-md mx-auto mt-1 mb-4">
            Get started right now using our 1-click bulk generator to automatically create wings, floors, and flats.
          </p>
          <Button
            size="sm"
            onClick={() => setShowBulkModal(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            <Sparkles className="h-3.5 w-3.5 mr-1.5" />
            <span>Launch Bulk Generator</span>
          </Button>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Building Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-zinc-200 dark:border-zinc-800">
            {buildings.map((b) => (
              <button
                key={b.id}
                onClick={() => setSelectedBuilding(b)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0 ${
                  selectedBuilding?.id === b.id
                    ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                    : 'bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100'
                }`}
              >
                <Building2 className="h-3.5 w-3.5" />
                <span>{b.name}</span>
              </button>
            ))}
          </div>

          {/* Floors & Units Display */}
          {floorsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
            </div>
          ) : floors.length === 0 ? (
            <div className="text-center py-12 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30">
              <Layers className="h-8 w-8 text-zinc-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">
                No floors found in {selectedBuilding?.name}
              </p>
              <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto mb-4">
                You can populate standard floors and flats into this wing in 1 instant API call, or add floors one by one.
              </p>
              <div className="flex justify-center gap-2">
                <Button
                  size="sm"
                  onClick={() => setShowQuickPopulateModal(true)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs h-8 flex items-center gap-1.5"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Populate Flats in this Wing</span>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setNewFloorNumber(0);
                    setNewFloorName('Ground Floor');
                    setShowAddFloorModal(true);
                  }}
                  className="text-xs h-8"
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  <span>Add First Floor</span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {floors.map((floor) => {
                const units = unitsByFloor[floor.id] || [];
                return (
                  <Card key={floor.id} className="border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
                    <CardHeader className="py-3 px-4 flex flex-row items-center justify-between border-b border-zinc-100 dark:border-zinc-900">
                      <div className="flex items-center gap-2">
                        <Layers className="h-4 w-4 text-zinc-500" />
                        <CardTitle className="text-sm font-semibold">
                          Floor {floor.floor_number} {floor.floor_name ? `(${floor.floor_name})` : ''}
                        </CardTitle>
                        <Badge variant="outline" className="text-[10px] text-zinc-500">
                          {units.length} Unit{units.length === 1 ? '' : 's'}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setEditingFloor(floor);
                            setEditFloorName(floor.floor_name || `Floor ${floor.floor_number}`);
                          }}
                          className="h-7 text-xs px-2 text-zinc-500 hover:text-zinc-700 flex items-center gap-1"
                          title="Rename Floor"
                        >
                          <Pencil className="h-3 w-3" />
                          <span className="hidden sm:inline">Rename</span>
                        </Button>

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteFloor(floor.id, floor.floor_name || `Floor ${floor.floor_number}`)}
                          className="h-7 text-xs px-2 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950 flex items-center gap-1"
                          title="Delete Floor"
                        >
                          <Trash2 className="h-3 w-3" />
                          <span className="hidden sm:inline">Delete</span>
                        </Button>

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setTargetFloorForUnit(floor);
                            setNewUnitNumber(`${floor.floor_number}${String(units.length + 1).padStart(2, '0')}`);
                          }}
                          className="h-7 text-xs px-2 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 dark:hover:bg-indigo-950 flex items-center gap-1"
                        >
                          <Plus className="h-3 w-3" />
                          <span>Add Flat</span>
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="p-4">
                      {units.length === 0 ? (
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-zinc-400 italic">No units registered on this floor.</p>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setTargetFloorForUnit(floor);
                              setNewUnitNumber(`${floor.floor_number}01`);
                            }}
                            className="h-7 text-[11px]"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            <span>Add Flat</span>
                          </Button>
                        </div>
                      ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                          {units.map((unit) => {
                            const isOccupied = unit.status === 'occupied';
                            return (
                              <div
                                key={unit.id}
                                onClick={() => {
                                  setEditingUnit({ unit, floorId: floor.id });
                                  setEditUnitNumber(unit.unit_number);
                                  setEditUnitType(unit.unit_type);
                                  setEditUnitStatus(unit.status);
                                }}
                                className={`p-3 rounded-lg border flex flex-col justify-between transition-all cursor-pointer hover:shadow-sm ${
                                  isOccupied
                                    ? 'border-emerald-200 bg-emerald-50/40 dark:border-emerald-900 dark:bg-emerald-950/20 hover:border-emerald-300'
                                    : 'border-zinc-200 bg-zinc-50/60 dark:border-zinc-800 dark:bg-zinc-900/40 hover:border-zinc-300'
                                }`}
                                title="Click to Edit or Delete Flat"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-1">
                                    <DoorOpen className="h-3.5 w-3.5 text-zinc-500" />
                                    <span>{unit.unit_number}</span>
                                  </span>
                                  <Badge
                                    variant="outline"
                                    className={`text-[9px] px-1 py-0 uppercase font-semibold ${
                                      isOccupied
                                        ? 'border-emerald-500 text-emerald-700 dark:text-emerald-400'
                                        : 'border-zinc-400 text-zinc-600 dark:text-zinc-400'
                                    }`}
                                  >
                                    {unit.status}
                                  </Badge>
                                </div>
                                <div className="mt-2 flex items-center justify-between text-[11px] text-zinc-500">
                                  <span className="capitalize">{unit.unit_type}</span>
                                  <Pencil className="h-3 w-3 text-zinc-400 opacity-60 hover:opacity-100" />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
