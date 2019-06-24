import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer, Human
from sc2.position import Point2, Point3

class SIMPLES(sc2.BotAI):
    #TODO build method is fine but it generates lots of log, on every try and fail. Maybe go back to previous way of building?
    hasCombatShield = False
    hasStimPack = False
    async def on_step(self, iteration):
        await self.Resources_Management()  
        await self.Military_Management()
        await self.Scout_Management()

    async def Scout_Management(self):
        await self.WalkingScout()
        await self.BuilderScout()
    
    async def WalkingScout(self):
        #print("TODO Walking Scout")
        return
    
    async def BuilderScout(self):
        #print("TODO Builder Scout")
        return
    
    async def Military_Management(self):
        #TODO rally troops in front of base
        if self.can_afford(MARINE):
            for barrack in self.units(BARRACKS).ready:
                if(barrack.is_idle) and self.supply_left > 1:
                    await self.do(barrack(BARRACKSTRAIN_MARINE))
                                        
                    if(barrack.add_on_tag != 0) and self.can_afford(MARINE):
                        #TODO discover what is the add_on_tag for reactor, to build 2 at a time on reactors
                        await self.do(barrack(BARRACKSTRAIN_MARINE))
                        #print("")

        if self.can_afford(MEDIVAC) and self.units(STARPORT).amount > 0:
            if self.units(MEDIVAC).amount < self.units(MARINE).amount/8:
                sp = self.units(STARPORT).first
                if sp.is_idle:
                    await self.do(sp(STARPORTTRAIN_MEDIVAC))
                

        await self.Research()
        await self.Armies()
    
    async def Research(self):
        cc = (self.units(COMMANDCENTER) | self.units(ORBITALCOMMAND)).first

        #TODO flags should only be set to true when research is finished
        if self.units(BARRACKSTECHLAB).idle and self.units(BARRACKSTECHLAB).ready:
            if not(self.hasCombatShield) and self.can_afford(RESEARCH_COMBATSHIELD):
                await self.do(self.units(BARRACKSTECHLAB).first(RESEARCH_COMBATSHIELD))
                self.hasCombatShield = True
            elif not(self.hasStimPack) and self.can_afford(BARRACKSTECHLABRESEARCH_STIMPACK):
                await self.do(self.units(BARRACKSTECHLAB).first(BARRACKSTECHLABRESEARCH_STIMPACK))    
                self.hasStimPack = True

        for idleBay in self.units(ENGINEERINGBAY).idle:
            if not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1) and not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1):
                await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL1))
            if not(UpgradeId.TERRANINFANTRYARMORSLEVEL1 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1) and not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1):
                await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1))
            if self.units(ARMORY).ready:
                if not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2) and not self.already_pending(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2))
                if not(UpgradeId.TERRANINFANTRYARMORSLEVEL2 in self.state.upgrades) and  self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2) and not self.already_pending(UpgradeId.TERRANINFANTRYARMORSLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2))
                if not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3) and not self.already_pending(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3))
                if not(UpgradeId.TERRANINFANTRYARMORSLEVEL3 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3) and not self.already_pending(UpgradeId.TERRANINFANTRYARMORSLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3))

    async def Armies(self):
        await self.ArmiesMacro()
        await self.ArmiesMicro()
    
    async def ArmiesMacro(self):
        #print("TODO Armies Macro")
        #basic strategy: swarm enemy with all armies
        if self.units(MARINE).amount > 70:
            for marine in self.units(MARINE):
                if not marine.is_attacking:
                    await self.do(marine.attack(self.enemy_start_locations[0]))

        #make medivac follow marines
        for medivac in self.units(MEDIVAC):
            if medivac.is_idle:
                soldierToFollow = self.units(MARINE).first
                await self.do(medivac.move(soldierToFollow.position))

    async def ArmiesMicro(self):
        #TODO make it so that marines dont block each other 
        
        #use stimpack when attacking, if not already under effect
        if self.hasStimPack:
            #TODO maybe refactor to improve peformance? 
            # we could search for a particular enemy unit, instead of iterating all of them
            for unit in self.known_enemy_units.not_structure:
                for marine in self.units(MARINE):
                    if not marine.has_buff(BuffId.STIMPACK) and marine.health > 20 and marine.target_in_range(unit):
                        await self.do(marine(EFFECT_STIM_MARINE))

    async def Resources_Management(self):
        await self.Collector()
        await self.Constructor()
    
    async def Collector(self):
        #print("TODO Collector")
        # manage collectors
        for center in self.townhalls:
            if center.ideal_harvesters > center.assigned_harvesters and self.can_afford(SCV) and center.is_idle:
                await self.do(center.train(SCV))

        # manage orbital energy and drop mules
        for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.state.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x:x.mineral_contents)
                await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

        #upgrade command centers to orbital command
        for cc in self.units(COMMANDCENTER):
            if self.can_afford(ORBITALCOMMAND) and cc.is_idle:
                await self.do(cc(UPGRADETOORBITAL_ORBITALCOMMAND))

        await self.distribute_workers()
        
        for a in self.units(REFINERY):
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w.exists:
                    await self.do(w.random.gather(a))

    async def Constructor(self):
        await self.RampBlocker()        
        
        # build refineries (on nearby vespene) when at least one SUPPLYDEPOT is in construction
        if self.units(SUPPLYDEPOT).amount > 0 and self.units(REFINERY).amount < 1:
            for th in self.townhalls:
                vgs = self.state.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place(REFINERY, vg.position) and self.can_afford(REFINERY):
                        # caution: the target for the refinery has to be the vespene geyser, not its position!
                        await self.do(self.getWorker().build(REFINERY, vg))

        cc = (self.units(COMMANDCENTER) | self.units(ORBITALCOMMAND)).first

        if self.units(BARRACKSREACTOR).amount > 0 and self.units(ENGINEERINGBAY).amount < 2 and self.can_afford(ENGINEERINGBAY):
            worker = self.getWorker()
            await self.build(ENGINEERINGBAY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)

        # expand if we can afford and have less than 2 bases
        if 1 <= self.townhalls.amount < 2 and self.already_pending(UnitTypeId.COMMANDCENTER) == 0 and self.can_afford(UnitTypeId.COMMANDCENTER):
            # get_next_expansion returns the center of the mineral fields of the next nearby expansion
            next_expo = await self.get_next_expansion()
            # from the center of mineral fields, we need to find a valid place to place the command center
            location = await self.find_placement(UnitTypeId.COMMANDCENTER, next_expo, placement_step=1)
            if location:
                # now we "select" (or choose) the nearest worker to that found location
                w = self.select_build_worker(location)
                if w and self.can_afford(UnitTypeId.COMMANDCENTER):
                    # the worker will be commanded to build the command center
                    error = await self.do(w.build(UnitTypeId.COMMANDCENTER, location))
                    if error:
                        print(error)

        # manage supplies
        if self.supply_left < 6 and self.supply_used >= 14 and self.can_afford(SUPPLYDEPOT) and self.units(SUPPLYDEPOT).not_ready.amount + self.already_pending(SUPPLYDEPOT) < 1:
            worker = self.getWorker()
            loc = await self.find_placement(SUPPLYDEPOT, worker.position, placement_step=3)
            await self.do(worker.build(SUPPLYDEPOT, loc))

        #building research buildings
        if self.units(FACTORY).amount + self.already_pending(FACTORY) == 0 and self.can_afford(FACTORY):
            worker = self.getWorker()
            await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)
        elif self.units(ARMORY).amount + self.already_pending(ARMORY) == 0 and self.can_afford(ARMORY):
            worker = self.getWorker()
            await self.build(ARMORY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)
        
        #TODO find a way to dont build barracks when add-on cant be built
        #sometimes barracks are built without space to add-ons
        #build 2 barracks, excluding the one from the ramp
        if self.units(BARRACKS).amount < 3 and self.can_afford(BARRACKS):
            worker = self.getWorker()
            next_expo = await self.get_next_expansion()
            location = await self.find_placement(UnitTypeId.BARRACKS, next_expo, placement_step=1)
            await self.build(BARRACKS, near=cc.position.towards(location, 20).random_on_distance(4), unit=worker)

        #every other barrack than the lab barrack should have reactor
        for rax in self.units(BARRACKS).ready:
            #print(rax.add_on_tag)
            if self.units(BARRACKSTECHLAB).amount == 0 and rax.add_on_tag == 0:
                if self.can_afford(BARRACKSTECHLAB):
                    await self.do(rax(BUILD_TECHLAB_BARRACKS))
            elif rax.add_on_tag == 0 and self.can_afford(BARRACKSREACTOR):            
                await self.do(rax(BUILD_REACTOR_BARRACKS))            

        #TODO check pre requirement to build a starport
        if self.units(STARPORT).amount == 0 and self.can_afford(STARPORT):
            worker = self.getWorker()
            await self.build(STARPORT, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)

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
                return            
            if barracks_placement_position:  # if workers were found              
                await self.do(self.getWorker().build(BARRACKS, barracks_placement_position))

        #barracks reactor upgrade on ramp
        if self.units(BARRACKSREACTOR).amount < 1 and self.units(BARRACKS).amount > 0:
            for barrack in self.units(BARRACKS).ready:
                if barrack.add_on_tag == 0:
                    await self.do(barrack(BUILD_REACTOR_BARRACKS))

    def getWorker(self):
        if self.workers.idle:
            #print("retornou um vagabundo")
            return self.workers.idle.random
        else:
            #print("retornou um trabalhador")
            return self.workers.gathering.random

def main():
    map = random.choice(
        [
            #"CatalystLE"
            # # Most maps have 2 upper points at the ramp (len(self.main_base_ramp.upper) == 2)
             #"AutomatonLE",
             #"BlueshiftLE",
             #"CeruleanFallLE",
             #"KairosJunctionLE",
             "ParaSiteLE",
             #"PortAleksanderLE",
             #"StasisLE",
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


