package in.agecm;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.*;
@Configuration @EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
 @Value("${agecm.origins}") String[] origins;
 public void configureMessageBroker(MessageBrokerRegistry r){r.enableSimpleBroker("/topic"); r.setApplicationDestinationPrefixes("/app");}
 public void registerStompEndpoints(StompEndpointRegistry r){r.addEndpoint("/ws").setAllowedOrigins(origins);}
}
