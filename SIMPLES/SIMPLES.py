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

        if self.can_afford(SCV) and self.workers.amount < 16 and cc.is_idle:
            await self.do(cc.train(SCV))

        await self.RampBlocker()        

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
        if depots.ready and self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
            if self.units(BARRACKS).amount + self.already_pending(BARRACKS) > 0:
                return
            
            if barracks_placement_position:  # if workers were found              
                await self.do(self.getWorker().build(BARRACKS, barracks_placement_position))




        if self.workers.amount > 30:
            for worker in self.workers:
                await self.do(worker.attack(self.enemy_start_locations[0]))

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
    sc2.run_game(
        sc2.maps.get(map), [Bot(Race.Terran, SIMPLES()), Computer(Race.Terran, Difficulty.Medium)], realtime=False
    )
    # sc2.run_game(
    #     sc2.maps.get(map), [Human(Race.Terran), Computer(Race.Zerg, Difficulty.VeryEasy)], realtime=True
    # )

if __name__ == "__main__":
    main()


