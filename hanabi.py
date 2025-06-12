import threading
import time
from broker.hanabi_broker import HanabiGameBroker
from publisher.hanabi_host import HanabiGameHost
from subscriber.hanabi_player import HanabiPlayer
import yaml


def hanabi(config):
    
    # game setup
    
    # broker = HanabiGameBroker(config)
    game = HanabiGameHost( config)

    game.game_loop()
    # game.display_with_gradio()
    # # loop
    # while game.state != "end":
    #     print("current state: " + game.state)
    #     if game.state == "start":
            
    #         game.game_start()
        
    #     elif game.state == "p1_choose_action":
            
            
    #         game.publish(game.state, game.to_dict())
    #         game.trigger('choose_done')
            
                
    #     elif game.state == "p1_give_clue":
            
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.clue_given()
                
            
    #     elif game.state == "p1_discard_card":
        
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.card_discarded()
            
                        
    #     elif game.state == "p1_play_card":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.card_played()
            
        
    #     elif game.state == "p1_done":
            
    #         game.p1_turn_end()
        
    #     elif game.state == "p2_choose_action":
            
    #         game.publish(game.state, game.to_dict())
    #         game.trigger('choose_done')
            
                
    #     elif game.state == "p2_give_clue":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.clue_given()
            
        
    #     elif game.state == "p2_discard_card":
            
    #         game.publish(game.state, game.to_dict())
    #         game.card_discarded()
            
                        
    #     elif game.state == "p2_play_card":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.card_played()
            
        
    #     elif game.state == "p2_done":
            
    #         game.p2_turn_end()


