import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer, Human
from sc2.position import Point2, Point3

class SIMPLES(sc2.BotAI):
    async def on_step(self, iteration):
        cc = self.units(COMMANDCENTER)
        if not cc.exists:
            return
        else:
            cc = cc.first

        if self.can_afford(SCV) and self.workers.amount < 20 and cc.is_idle:
            await self.do(cc.train(SCV))

        await self.Resources_Management()  
        await self.Military_Management()
        await self.Scout_Management()

        if self.units(MARINE).amount > 20:
            for marine in self.units(MARINE):
                await self.do(marine.attack(self.enemy_start_locations[0]))


    async def Scout_Management(self):
        await self.WalkingScout()
        await self.BuilderScout()
    
    async def WalkingScout(self):
        print("TODO Walking Scout")
    
    async def BuilderScout(self):
        print("TODO Builder Scout")
    
    async def Military_Management(self):
        if self.can_afford(MARINE):
            for barrack in self.units(BARRACKS):
                if(barrack.is_idle):
                    await self.do(barrack(BARRACKSTRAIN_MARINE))
                    if(barrack.add_on_tag != 0):
                        await self.do(barrack(BARRACKSTRAIN_MARINE))

        await self.Research()
        await self.Armies()
    async def Research(self):
        if self.units(BARRACKSREACTOR).amount > 0 and self.units(ENGINEERINGBAY).amount < 2 and self.can_afford(ENGINEERINGBAY):
            worker = self.getWorker()
            loc = await self.find_placement(ENGINEERINGBAY, worker.position, placement_step=3)
            await self.do(worker.build(ENGINEERINGBAY, loc))

        for idleBay in self.units(ENGINEERINGBAY).idle:
            if not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1):
                await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1))
            if not(UpgradeId.TERRANINFANTRYARMORSLEVEL1 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1):
                await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1))
            if self.units(ARMORY).amount > 0:
                if self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2))
                if self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2))
                if self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3))
                if self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3))
            elif self.can_afford(ARMORY):
                # Not working, cant manage to build armory
                worker = self.getWorker()
                loc = await self.find_placement(ARMORY, worker.position)
                await self.do(worker.build(ARMORY, loc))

    async def Armies(self):
        await self.ArmiesMacro()
        await self.ArmiesMicro()
    async def ArmiesMacro(self):
        print("TODO Armies Macro")
    async def ArmiesMicro(self):
        print("TODO Armies Micro")
    async def Resources_Management(self):
        await self.Collector()
        await self.Constructor()
    async def Collector(self):
        print("TODO Collector")
        self.distribute_workers()
        # build refineries (on nearby vespene) when at least one SUPPLYDEPOT is in construction
        if self.units(SUPPLYDEPOT).amount > 0 and self.units(REFINERY).amount < 1:
            for th in self.townhalls:
                vgs = self.state.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place(REFINERY, vg.position) and self.can_afford(REFINERY):
                        # caution: the target for the refinery has to be the vespene geyser, not its position!
                        await self.do(self.getWorker().build(REFINERY, vg))

        for a in self.units(REFINERY):
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w.exists:
                    await self.do(w.random.gather(a))

        # do something with idle SCVs
        # for scv in self.units(SCV).idle:
        #     await self.do(scv.gather(self.state.mineral_field.closest_to(cc)))

    async def Constructor(self):
        await self.RampBlocker()
        
        if self.supply_left < 4 and self.supply_used >= 14 and self.can_afford(SUPPLYDEPOT) and self.units(SUPPLYDEPOT).not_ready.amount + self.already_pending(SUPPLYDEPOT) < 1:
            worker = self.getWorker()
            loc = await self.find_placement(SUPPLYDEPOT, worker.position, placement_step=3)
            await self.do(worker.build(SUPPLYDEPOT, loc))

        #building research buildings
        if self.units(FACTORY).amount == 0 and self.can_afford(FACTORY):
            worker = self.getWorker()
            loc = await self.find_placement(FACTORY, worker.position)
            await self.do(worker.build(FACTORY, loc))
        elif self.units(ARMORY).amount == 0 and self.can_afford(ARMORY):
            worker = self.getWorker()
            loc = await self.find_placement(ARMORY, worker.position)
            await self.do(worker.build(ARMORY, loc))

        
        if self.units(BARRACKSTECHLAB).amount == 0 and self.can_afford(BARRACKSTECHLAB):
            worker = self.getWorker()
            loc = await self.find_placement(BARRACKS, worker.position)
            await self.do(worker.build(BARRACKS, loc))
            for rax in self.units(BARRACKS):
                if rax.add_on_tag == 0:
                    await self.do(rax(BUILD_TECHLAB_BARRACKS))



    async def RampBlocker(self):
        # Raise depos when enemies are nearby
        for depo in self.units(SUPPLYDEPOT).ready:
            for unit in self.known_enemy_units.not_structure:
                if unit.position.to2.distance_to(depo.position.to2) < 15:
                    break
            else:
                await self.do(depo(MORPH_SUPPLYDEPOT_LOWER))

        # Lower depos when no enemies are nearby
        for depo in self.units(SUPPLYDEPOTLOWERED).ready:
            for unit in self.known_enemy_units.not_structure:
                if unit.position.to2.distance_to(depo.position.to2) < 10:
                    await self.do(depo(MORPH_SUPPLYDEPOT_RAISE))
                    break

        depot_placement_positions = self.main_base_ramp.corner_depots

        barracks_placement_position = self.main_base_ramp.barracks_correct_placement

        depots = self.units(SUPPLYDEPOT) | self.units(SUPPLYDEPOTLOWERED)

        # Filter locations close to finished supply depots
        if depots:
            depot_placement_positions = {d for d in depot_placement_positions if depots.closest_distance_to(d) > 1}

        #barracks reactor upgrade on ramp
        if self.units(BARRACKSREACTOR).amount < 1 and self.units(BARRACKS).amount > 0:
            for barrack in self.units(BARRACKS).ready:
                if barrack.add_on_tag == 0:
                    await self.do(barrack(BUILD_REACTOR_BARRACKS))

        # Build depots
        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
            if len(depot_placement_positions) == 0:
                return
            # Choose any depot location
            target_depot_location = depot_placement_positions.pop()                            
            await self.do(self.getWorker().build(SUPPLYDEPOT, target_depot_location))

        # Build barracks
        if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
            if self.units(BARRACKS).amount + self.already_pending(BARRACKS) > 0:
                print("---------------------------------------------------------------------")
                return            
            if barracks_placement_position:  # if workers were found              
                await self.do(self.getWorker().build(BARRACKS, barracks_placement_position))


    def getWorker(self):
        if self.workers.idle:
            print("retornou um vagabundo")
            return self.workers.idle.random
        else:
            print("retornou um trabalhador")
            return self.workers.gathering.random

def main():
    map = random.choice(
        [
            "CatalystLE"
            # # Most maps have 2 upper points at the ramp (len(self.main_base_ramp.upper) == 2)
            # "AutomatonLE",
            # "BlueshiftLE",
            # "CeruleanFallLE",
            # "KairosJunctionLE",
            # "ParaSiteLE",
            # "PortAleksanderLE",
            # "StasisLE",
            # #"DarknessSanctuaryLE",
            # #"SequencerLE", # Upper right has a different ramp top
            # "ParaSiteLE",  # Has 5 upper points at the main ramp
            # #"AcolyteLE",  # Has 4 upper points at the ramp to the in-base natural and 2 upper points at the small ramp
            # #"HonorgroundsLE",  # Has 4 or 9 upper points at the large main base ramp
        ]
    )
    sc2.run_game(sc2.maps.get(map), [
            Bot(Race.Terran, SIMPLES()), 
            Computer(Race.Terran, Difficulty.Medium)
        ], realtime=False
    )
    

if __name__ == "__main__":
    main()


