
from broker.codenames_broker import CodenamesGameBroker
from publisher.codenames_host import CodenamesGameHost

            
def codenames(config):
    
    # broker = CodenamesGameBroker(config)
    game = CodenamesGameHost(config)
    
    game.game_loop()
    # while game.state != "end":
    #     print("current state: " + game.state)
    #     if game.state == "start":

    #         game.game_start()
        
    #     elif game.state == "red_spymaster_give_clue":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.clue_given()
            
        
    #     elif game.state == "red_operative_guess":
            
    #         game.publish(game.state, game.to_dict())
                 
    #         game.guess_made()
        
    #     elif game.state == "red_operative_guess_made":
    #         game.guess_made()
            
    #     elif game.state == "blue_spymaster_give_clue":
            
    #         game.publish(game.state, game.to_dict())
            
            
    #         game.clue_given()
        
    #     elif game.state == "blue_operative_guess":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.guess_made()
    
    #     elif game.state == "blue_operative_guess_made":
    #         game.guess_made()
            
    
    # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    # with open(f"logs/codenames/obs-{t}.log", "w") as f:
    #     # save
    #     for i in game.log:
    #         print(i)
    #         f.write(str(i) + "\n")
            
            
# if __name__ == "__main__":
#     codenames()
