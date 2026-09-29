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

  // Single Building State
  const [showAddBuilding, setShowAddBuilding] = useState(false);
  const [newBuildingName, setNewBuildingName] = useState('');

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
  useEffect(() => {
    if (!societyId || !selectedBuilding) return;

    let isMounted = true;
    const fetchFloorsAndUnits = async () => {
      setFloorsLoading(true);
      try {
        const floorRes = await apiClient.get(
          `/societies/${societyId}/buildings/${selectedBuilding.id}/floors`
        );
        const floorList: Floor[] = floorRes.data?.data || floorRes.data || [];
        if (!isMounted) return;
        setFloors(Array.isArray(floorList) ? floorList : []);

        // Fetch units for each floor in parallel
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
        if (!isMounted) return;
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
        if (isMounted) setFloorsLoading(false);
      }
    };

    fetchFloorsAndUnits();

    return () => {
      isMounted = false;
    };
  }, [societyId, selectedBuilding]);

  // Bulk Provision Action
  const handleBulkProvision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      await apiClient.post(`/societies/${societyId}/provision`, {
        buildings: [
          {
            name: bulkTowerName.trim(),
            number_of_floors: Number(bulkNumFloors),
            units_per_floor: Number(bulkUnitsPerFloor),
          },
        ],
      });
      setFeedback({
        type: 'success',
        message: `Successfully provisioned ${bulkTowerName} with ${bulkNumFloors} floors and ${bulkNumFloors * bulkUnitsPerFloor} units!`,
      });
      setShowBulkModal(false);
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

  // Create Single Building
  const handleCreateBuilding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!societyId || !newBuildingName.trim()) return;

    setActionLoading(true);
    setFeedback(null);

    try {
      const res = await apiClient.post(`/societies/${societyId}/buildings`, {
        name: newBuildingName.trim(),
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

      {/* Bulk Provisioning Modal Drawer */}
      {showBulkModal && (
        <Card className="border-2 border-indigo-200 dark:border-indigo-900 bg-indigo-50/50 dark:bg-indigo-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-indigo-950 dark:text-indigo-200 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              <span>Bulk Society Structure Provisioning</span>
            </CardTitle>
            <CardDescription className="text-xs text-zinc-600 dark:text-zinc-400">
              Instantly generate an entire building tower with numbered floors and individual flat units in one transaction.
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
                  Units Per Floor (1-20)
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
                  <span>Generate {bulkNumFloors * bulkUnitsPerFloor} Flats Now</span>
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
            <div className="text-center py-12 border border-dashed rounded-xl border-zinc-200 dark:border-zinc-800">
              <Layers className="h-8 w-8 text-zinc-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                No floors found in {selectedBuilding?.name}
              </p>
              <p className="text-xs text-zinc-500 mt-1">
                Use the bulk generator or floor creation API to set up flats in this wing.
              </p>
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
                    </CardHeader>
                    <CardContent className="p-4">
                      {units.length === 0 ? (
                        <p className="text-xs text-zinc-400 italic">No units registered on this floor.</p>
                      ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                          {units.map((unit) => {
                            const isOccupied = unit.status === 'occupied';
                            return (
                              <div
                                key={unit.id}
                                className={`p-3 rounded-lg border flex flex-col justify-between transition-all ${
                                  isOccupied
                                    ? 'border-emerald-200 bg-emerald-50/40 dark:border-emerald-900 dark:bg-emerald-950/20'
                                    : 'border-zinc-200 bg-zinc-50/60 dark:border-zinc-800 dark:bg-zinc-900/40'
                                }`}
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
                                  <ChevronRight className="h-3 w-3 text-zinc-400" />
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
