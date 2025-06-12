
from broker.azul_broker import AzulGameBroker
from publisher.azul_host import AzulGameHost


            
def logging(content):
    print(content)


def azul(config):
    

    # broker = AzulGameBroker(config)
    game = AzulGameHost(config)

    game.game_loop()

    # while game.state != "end":
    #     print("current state: " + game.state)
    #     if game.state == "start":
    #         game.game_start()
        
    #     elif game.state == "round_start":
            
    #         game.new_round()
            
    #     elif game.state == "p1_turn":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.p1_done()
            
    #     elif game.state == "p1_turn_end":
            
            
    #         game.p1_done()
            
    #     elif game.state == "p2_turn":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.p2_done()
            
    #     elif game.state == "p2_turn_end":
            
            
    #         game.p2_done()
        
    #     elif game.state == "round_end":
            
    #         game.round_end()
            
    #     elif game.state == "score_count":
            
            
    #         game.game_end()
    
    # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    # with open(f"logs/azul/obs-{t}.log", "w") as f:
    #     # save
    #     for i in game.log:
    #         print(i)
    #         f.write(str(i) + "\n")
            
            
if __name__ == "__main__":
    azul()