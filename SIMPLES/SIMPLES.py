import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random, numpy as np

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer, Human
from sc2.position import Point2, Point3
from sc2.data import Race

class SIMPLES(sc2.BotAI):
    #TODO build method is fine but it generates lots of log, on every try and fail. Maybe go back to previous way of building?
    hasCombatShield = False
    hasStimPack = False
    scouter_tag = None
    scouterGoingEnemy = True
    scouterNumber = 0

    @property
    def DIST_THRESHOLD(self):
        return 5 + (10*self.scouterNumber)

    async def on_step(self, iteration):
        await self.Scout_Management()
        await self.Resources_Management()  
        await self.Military_Management(iteration)

    async def Scout_Management(self):
        await self.WalkingScout()
        await self.BuilderScout()
    
    async def WalkingScout(self):
        scouter = self.getScouter()
        if scouter is None:
            return

        # If enemies found, run or fight
        close_enemies = self.state.units.closer_than(15, scouter.position).filter(lambda unit: unit.is_enemy)
        if close_enemies.amount > 1:
            self.scouterGoingEnemy = False
            await self.do(scouter.move(self.start_location))
            return
        elif close_enemies.amount == 1:
            enemy = close_enemies[0]
            if enemy.race == Race.Zerg:
                self.scouterGoingEnemy = False
                await self.do(scouter.move(self.start_location))
            else:
                await self.do(scouter.attack(enemy.position))

        # If no enemies, keep walking around
        enemy_dist = scouter.position.distance_to(self.enemy_start_locations[0])
        start_dist = scouter.position.distance_to(self.start_location)

        if self.scouterGoingEnemy and enemy_dist > self.DIST_THRESHOLD:
            await self.do(scouter.move(self.enemy_start_locations[0]))
        elif enemy_dist < self.DIST_THRESHOLD:
            self.scouterGoingEnemy = False
            await self.do(scouter.move(self.start_location))
        elif not self.scouterGoingEnemy:
            if start_dist < self.DIST_THRESHOLD:
                self.scouterGoingEnemy = True
                await self.do(scouter.move(self.enemy_start_locations[0]))
            else:
                await self.do(scouter.move(self.start_location))
    
    async def BuilderScout(self):
        scouter = self.getScouter()
        if scouter is None:
            return

        enemy_dist = scouter.position.distance_to(self.enemy_start_locations[0])
        start_dist = scouter.position.distance_to(self.start_location)

        # 2 minutes passed                                      try around middle of the map
        if self.time > 2*60 and self.can_afford(SENSORTOWER) and abs(enemy_dist - start_dist) < 50:

            # Avoid building towers near to each other
            exist_tower_near = False
            for tower in self.units(SENSORTOWER):
                if scouter.position.distance_to(tower.position) < 30:
                    exist_tower_near = True

            if not exist_tower_near:
                await self.do(scouter.build(SENSORTOWER, scouter.position))
  
    async def Military_Management(self, iteration):
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
        await self.Armies(iteration)
    
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
            elif not(UpgradeId.TERRANINFANTRYARMORSLEVEL1 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1) and not self.already_pending_upgrade(UpgradeId.TERRANINFANTRYARMORSLEVEL1):
                await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL1))
            elif self.units(ARMORY).ready and self.hasStimPack and self.hasCombatShield: #stablish research priority
                if not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2) and not self.already_pending(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL2))
                elif not(UpgradeId.TERRANINFANTRYARMORSLEVEL2 in self.state.upgrades) and  self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2) and not self.already_pending(UpgradeId.TERRANINFANTRYARMORSLEVEL2):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL2))
                elif not(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3) and not self.already_pending(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYWEAPONSLEVEL3))
                elif not(UpgradeId.TERRANINFANTRYARMORSLEVEL3 in self.state.upgrades) and self.can_afford(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3) and not self.already_pending(UpgradeId.TERRANINFANTRYARMORSLEVEL3):
                    await self.do(idleBay(ENGINEERINGBAYRESEARCH_TERRANINFANTRYARMORLEVEL3))

    async def Armies(self, iteration):
        await self.ArmiesMacro()
        await self.ArmiesMicro(iteration)
    
    async def ArmiesMacro(self):
        #TODO: rally troops in a defensive way
        #print("TODO Armies Macro")
        #basic strategy: swarm enemy with all armies
        if self.units(MARINE).amount > 70:
            for marine in self.units(MARINE):
                if not marine.is_attacking:
                    await self.do(marine.attack(self.enemy_start_locations[0]))

        #make medivac follow marines
        for medivac in self.units(MEDIVAC):
            if medivac.is_idle:
                marines = self.units(MARINE)
                if marines.amount == 0:
                    await self.do(medivac.move(self.start_location))
                    continue
                
                marines = marines.sorted(lambda unit: unit.health + medivac.position.distance_to(unit.position))
                await self.do(medivac.move(marines.first.position))

    async def ArmiesMicro(self, iteration):
        #TODO make it so that marines dont block each other 
        
        #use stimpack when attacking, if not already under effect
        if self.hasStimPack:
            #TODO if enemy moves away from main base, our troops keep gathering there forerever
            #TODO try to improve performance, this way is almost the same as previou way
            if iteration % 4 == 0:
                for marine in self.units(MARINE):
                    if not marine.has_buff(BuffId.STIMPACK) and marine.health > 20 and self.known_enemy_units.not_structure.in_attack_range_of(marine):
                        await self.do(marine(EFFECT_STIM_MARINE))

    async def Resources_Management(self):
        await self.Collector()
        await self.Constructor()
    
    async def Collector(self):
        #print("TODO Collector")
        # manage collectors
        for center in self.townhalls:
            if center.ideal_harvesters > center.assigned_harvesters-1 and self.can_afford(SCV) and center.is_idle:
                await self.do(center.train(SCV))

        # manage orbital energy and drop mules
        for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.state.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x:x.mineral_contents)
                await self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

        #upgrade command centers to orbital command
        if self.units(BARRACKS).ready.amount > 0:
            for cc in self.units(COMMANDCENTER).ready:
                if self.can_afford(ORBITALCOMMAND) and cc.is_idle and not self.already_pending(ORBITALCOMMAND):
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
        refineriesToBuild = 1
        ccs = self.units(COMMANDCENTER).amount + self.units(ORBITALCOMMAND).amount
        if ccs > 1:
            refineriesToBuild = 2
        if self.units(SUPPLYDEPOT).amount > 0 and self.units(REFINERY).amount < refineriesToBuild:
            for th in self.townhalls:
                vgs = self.state.vespene_geyser.closer_than(10, th)
                for vg in vgs:
                    if await self.can_place(REFINERY, vg.position) and self.can_afford(REFINERY):
                        # caution: the target for the refinery has to be the vespene geyser, not its position!
                        await self.do(self.getWorker().build(REFINERY, vg))

        cc = (self.units(COMMANDCENTER) | self.units(ORBITALCOMMAND))[-1]

        if self.units(BARRACKSREACTOR).amount > 0 and (self.already_pending(ENGINEERINGBAY) + self.units(ENGINEERINGBAY).amount) < 2 and self.can_afford(ENGINEERINGBAY):
            worker = self.getWorker()
            await self.build(ENGINEERINGBAY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)

        # TODO: Expand right (today expansions may be hard because barracks placement are near next base)
        #expand if we can afford and have less than 2 bases
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
        if self.units(FACTORY).amount + self.already_pending(FACTORY) == 0 and self.can_afford(FACTORY) and self.units(BARRACKS).ready.amount > 1:
            worker = self.getWorker()
            await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)
        elif self.units(ARMORY).amount + self.already_pending(ARMORY) == 0 and self.can_afford(ARMORY) and self.units(FACTORY).ready.amount > 0:
            worker = self.getWorker()
            await self.build(ARMORY, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)
        
        if self.units(STARPORT).amount == 0 and self.can_afford(STARPORT) and self.units(FACTORY).ready.amount > 0:
            worker = self.getWorker()
            await self.build(STARPORT, near=cc.position.towards(self.game_info.map_center, 10).random_on_distance(4), unit=worker)
        
        #TODO find a way to dont build barracks when add-on cant be built
        #sometimes barracks are built without space to add-ons
        #build 2 barracks, excluding the one from the ramp
        #barracks are 3x3 and with addon are basically 3x5
        if (self.already_pending(COMMANDCENTER) + ccs) > 1:
            if (self.units(BARRACKS).amount + self.already_pending(BARRACKS)) < 3 and self.units(BARRACKS).amount > 0 and self.can_afford(BARRACKS) and self.units(ORBITALCOMMAND).amount > 0:
                worker = self.getWorker()
                next_expo = (self.units(COMMANDCENTER) | self.units(ORBITALCOMMAND)).first.position
                location = await self.find_placement(UnitTypeId.COMMANDCENTER, next_expo, placement_step=1)
                await self.build(BARRACKS, near=location, unit=worker)

        #every other barrack than the lab barrack should have reactor
        if self.units(BARRACKS).ready.amount > 1:
            for rax in self.units(BARRACKS).ready:
                #print(rax.add_on_tag)
                if rax.add_on_tag == 0 and self.can_afford(BARRACKSREACTOR):            
                    await self.do(rax(BUILD_REACTOR_BARRACKS))         

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

        if self.units(BARRACKSTECHLAB).amount > 0:
            return

        depot_placement_positions = self.main_base_ramp.corner_depots

        barracks_placement_position = self.main_base_ramp.barracks_correct_placement

        depots = self.units(SUPPLYDEPOT) | self.units(SUPPLYDEPOTLOWERED)

        # Filter locations close to finished supply depots
        if depots:
            depot_placement_positions = {d for d in depot_placement_positions if depots.closest_distance_to(d) > 1}

        # Build depots
        if self.can_afford(SUPPLYDEPOT) and not self.already_pending(SUPPLYDEPOT):
            if len(depot_placement_positions) != 0:    
                target_depot_location = depot_placement_positions.pop()                            
                await self.do(self.getWorker().build(SUPPLYDEPOT, target_depot_location))

        # Build barracks
        if self.can_afford(BARRACKS):
            if self.units(BARRACKS).amount + self.already_pending(BARRACKS) == 0:
                if barracks_placement_position:  # if workers were found           
                    await self.do(self.getWorker().build(BARRACKS, barracks_placement_position))

        #barracks reactor upgrade on ramp
        if self.units(BARRACKSTECHLAB).amount < 1 and self.units(BARRACKS).ready.amount > 0 and self.can_afford(BARRACKSTECHLAB) and not self.already_pending(BARRACKSTECHLAB):
            barrack = self.units(BARRACKS).ready.first
            if barrack.add_on_tag == 0:
                await self.do(barrack(BUILD_TECHLAB_BARRACKS))

    def getWorker(self):
        if self.workers.idle:
            #print("retornou um vagabundo")
            return self.workers.idle.random
        else:
            #print("retornou um trabalhador")
            return self.workers.gathering.random

    def getIDLEWorker(self):
        if self.workers.idle:
            return self.workers.idle.random
        return None
    
    def getScouter(self):
        if self.scouter_tag is not None:
            try:
                return self.units.by_tag(self.scouter_tag)
            except:
                # Had scout but now it's dead
                self.scouter_tag = None
                self.scouterGoingEnemy = True
                self.scouterNumber += 1
                return self.getScouter()

        idle_worker = self.getIDLEWorker()
        if idle_worker is not None:
            self.scouter_tag = idle_worker.tag
            return self.units.by_tag(self.scouter_tag)
        return None


def main():
    map = random.choice(
        [
            #"CatalystLE"
            # # Most maps have 2 upper points at the ramp (len(self.main_base_ramp.upper) == 2)
             "AutomatonLE",
             "BlueshiftLE",
             "CeruleanFallLE",
             "KairosJunctionLE",
             "ParaSiteLE",
             "PortAleksanderLE",
             "StasisLE",
             "DarknessSanctuaryLE",
            # #"SequencerLE", # Upper right has a different ramp top
            # "ParaSiteLE",  # Has 5 upper points at the main ramp
            # #"AcolyteLE",  # Has 4 upper points at the ramp to the in-base natural and 2 upper points at the small ramp
            # #"HonorgroundsLE",  # Has 4 or 9 upper points at the large main base ramp
        ]
    )
    sc2.run_game(sc2.maps.get(map), [
            Bot(Race.Terran, SIMPLES()), 
            Computer(Race.Terran, Difficulty.VeryEasy)
        ], realtime=False
    )
    

if __name__ == "__main__":
    main()


