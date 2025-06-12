
from broker.catan_broker import CatanBroker
from publisher.catan_host import CatanHost


            
def logging(content):
    print(content)


def catan(config):
    
    broker = CatanBroker(config)
    game = CatanHost(broker)


    while game.state != "end":
        print("current state: " + game.state)
        
        if game.state == "game_start":
            game.next()
        
        elif game.state == 'initial_phase':
            game.next()
        
        elif game.state == 'place_initial_settlements':
            
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'place_initial_roads':
            
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'initial_phase_end':
            game.next()
        
        elif game.state == 'production_phase':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'roll_dice':
            game.publish(game.state, game.to_dict())
            game.next()
            
        elif game.state == 'production_phase_end':
            game.next()
        
        elif game.state == 'trade_n_build_phase':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'trade_n_build_phase_end':
            game.next()
        
        elif game.state == 'trade':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'response_to_trade':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'maritime_trade':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'build_road':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'build_settlement':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'build_city':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'buy_development_card':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'play_development_card':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'robbery_phase':
            # game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'move_robber':
            game.publish(game.state, game.to_dict())
            game.next()
        
        elif game.state == 'robbery_phase_end':
            game.next()
        
        
            
            # 'game_end',
            # 'end'